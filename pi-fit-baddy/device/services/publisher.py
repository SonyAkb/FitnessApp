"""Publisher: отправка показаний Sampler в backend (PI-09).

Раз в `PUBLISH_INTERVAL_SECONDS` снимает `Sampler.current()`, собирает
TelemetryDTO(source=raspberry_pi) по `docs/API_CONTRACT.md` и шлёт его в
`POST /api/v1/telemetry/ingest` с заголовком `X-Device-Token`. Неотправленные
точки лежат в ограниченном буфере в памяти и повторяются на следующих циклах
(доставка «минимум один раз»: идемпотентности в контракте нет).
`steps` — накопленное число шагов с запуска сервиса (как в `/device/vitals/current`),
поэтому пропуск точки без валидного пульса шагов не теряет: следующая отправленная
точка несёт полный итог.
Работает в том же цикле событий, что и Sampler, блокировки не нужны.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from device.clock import Clock, MonotonicClock
from device.config import Config
from device.services.sampler import Reading, Sampler
from device.timefmt import format_timestamp

# Собственные решения: ≈ 8 минут данных при интервале 5 с; таймаут HTTP 5 с.
BUFFER_MAX_POINTS = 100
HTTP_TIMEOUT_S = 5.0
INGEST_PATH = "/api/v1/telemetry/ingest"
HEART_RATE_MIN = 30
HEART_RATE_MAX = 230
_RETRYABLE_4XX = {408, 429}

logger = logging.getLogger(__name__)


class Publisher:
    def __init__(
        self,
        sampler: Sampler,
        client: httpx.AsyncClient,
        *,
        backend_url: str,
        device_id: str,
        device_token: str,
        interval_s: float,
        calories_per_step: float,
        clock: Clock | None = None,
        buffer_max: int = BUFFER_MAX_POINTS,
    ) -> None:
        backend_url = (backend_url or "").strip()
        device_id = (device_id or "").strip()
        device_token = (device_token or "").strip()
        missing = [
            name
            for name, value in (
                ("BACKEND_URL", backend_url),
                ("DEVICE_ID", device_id),
                ("DEVICE_TOKEN", device_token),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "PUBLISH_ENABLED=true, но не заданы: " + ", ".join(missing)
            )
        parts = urlsplit(backend_url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("BACKEND_URL должен быть вида http(s)://host[:port]")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in device_token):
            raise ValueError("DEVICE_TOKEN содержит управляющие символы")
        if interval_s < 1:
            raise ValueError("PUBLISH_INTERVAL_SECONDS должен быть >= 1")
        self._sampler = sampler
        self._client = client
        self._url = backend_url.rstrip("/") + INGEST_PATH
        self._device_id = device_id
        self._token = device_token
        self._interval = float(interval_s)
        self._calories_per_step = calories_per_step
        self._clock = clock or MonotonicClock()
        self._buffer: deque[dict[str, Any]] = deque(maxlen=buffer_max)

    @classmethod
    def from_config(
        cls,
        config: Config,
        sampler: Sampler,
        client: httpx.AsyncClient,
        clock: Clock | None = None,
    ) -> Publisher:
        return cls(
            sampler,
            client,
            backend_url=config.backend_url or "",
            device_id=config.device_id or "",
            device_token=config.device_token or "",
            interval_s=config.publish_interval_seconds,
            calories_per_step=config.calories_per_step,
            clock=clock,
        )

    def __repr__(self) -> str:
        return f"Publisher(url={self._url!r}, device_id={self._device_id!r})"

    @property
    def pending(self) -> int:
        """Сколько точек ждёт отправки."""
        return len(self._buffer)

    async def run(self, sleep: Callable[[float], Any] = asyncio.sleep) -> None:
        """Цикл по расписанию Clock без накопления дрейфа; первая отправка
        через один интервал. Исключения цикла логируются, задача живёт."""
        next_at = self._clock.now()
        while True:
            next_at += self._interval
            delay = next_at - self._clock.now()
            if delay < 0:
                next_at = self._clock.now()
                delay = 0.0
            await sleep(delay)
            try:
                await self.publish_once()
            except Exception as exc:
                logger.error(
                    "Сбой цикла публикации (%s); продолжаем", type(exc).__name__
                )

    async def publish_once(self) -> None:
        """Один цикл: снять показание, поставить в буфер, отправить от старых к новым."""
        payload = self._payload(self._sampler.current())
        if payload is not None:
            if len(self._buffer) == self._buffer.maxlen:
                logger.warning(
                    "Буфер переполнен (%d): вытеснена самая старая точка",
                    self._buffer.maxlen,
                )
            self._buffer.append(payload)
        await self._flush()

    # --- внутреннее -----------------------------------------------------

    def _payload(self, reading: Reading) -> dict[str, Any] | None:
        hr = reading.heart_rate
        if hr is None or not HEART_RATE_MIN <= hr <= HEART_RATE_MAX:
            logger.debug("Точка пропущена: нет валидного пульса (%s)", hr)
            return None
        return {
            "device_id": self._device_id,
            "steps": reading.steps,
            "heart_rate": hr,
            "calories": round(reading.steps * self._calories_per_step),
            "timestamp": format_timestamp(reading.timestamp),
            "source": "raspberry_pi",
        }

    async def _flush(self) -> None:
        while self._buffer:
            if not await self._send(self._buffer[0]):
                return  # порядок сохраняется: первая неудача прерывает цикл
            self._buffer.popleft()

    async def _send(self, payload: dict[str, Any]) -> bool:
        """True — точку можно убрать из буфера (принята или отвергнута навсегда)."""
        try:
            response = await self._client.post(
                self._url,
                json=payload,
                headers={"X-Device-Token": self._token},
                timeout=HTTP_TIMEOUT_S,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "Backend недоступен (%s); в буфере %d", type(exc).__name__, self.pending
            )
            return False
        code = response.status_code
        if 200 <= code < 300:
            return True
        if code >= 500 or code in _RETRYABLE_4XX:
            logger.warning("Backend ответил %d; повтор позже", code)
            return False
        if 300 <= code < 400:
            logger.error(
                "Backend ответил редиректом (%d): проверьте BACKEND_URL "
                "(возможно, нужен https вместо http); точка отброшена",
                code,
            )
        elif code in (401, 403):
            logger.error(
                "Backend отклонил точку (%d): проверьте DEVICE_ID и DEVICE_TOKEN", code
            )
        else:
            logger.error("Backend отклонил точку (%d); точка отброшена", code)
        return True
