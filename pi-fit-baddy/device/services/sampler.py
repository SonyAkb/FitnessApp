"""Sampler: опрос датчиков, кольцевая история измерений (PI-08).

`tick()` — один шаг опроса без `sleep` и без привязки к реальному времени;
время берётся из внедряемого `Clock`, календарная метка — из `utc_now`.
Цикл `run()` лишь вызывает `tick()` по расписанию. Объект принадлежит одному
циклу событий: и цикл опроса, и обработчики API (`async def`) работают в одном
потоке, поэтому блокировки не нужны.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from device.bus.factory import create_bus
from device.clock import Clock, MonotonicClock
from device.config import Config
from device.drivers.max30102 import Max30102
from device.drivers.mpu6050 import Mpu6050
from device.services.heart_rate import HeartRateEstimator
from device.services.step_counter import StepCounter

# Собственное решение: точка истории не чаще раза в секунду (по Clock),
# иначе при 50 Гц буфер в 3600 точек покрывал бы 72 секунды.
HISTORY_INTERVAL_S = 1.0

logger = logging.getLogger(__name__)


def _default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Reading:
    """Одно измерение: пульс (None — нет оценки), шаги, момент UTC."""

    heart_rate: int | None
    steps: int
    timestamp: datetime


class Sampler:
    def __init__(
        self,
        config: Config,
        bus: Any,
        clock: Clock,
        utc_now: Callable[[], datetime] = _default_utc_now,
    ) -> None:
        self.config = config
        self._clock = clock
        self._utc_now = utc_now
        self._mpu = Mpu6050(bus, config.mpu6050_addr)
        self._max = Max30102(bus, config.max30102_addr)
        self._steps = StepCounter.from_config(config, clock)
        self._hr = HeartRateEstimator.from_config(config, clock)
        self._history: deque[Reading] = deque(maxlen=config.history_max_points)
        self._last_history_at: float | None = None
        self._mpu_ready = False
        self._max_ready = False
        self._mpu_ok = False
        self._max_ok = False

    @classmethod
    def from_config(
        cls,
        config: Config,
        clock: Clock | None = None,
        utc_now: Callable[[], datetime] = _default_utc_now,
    ) -> Sampler:
        return cls(config, create_bus(config), clock or MonotonicClock(), utc_now)

    @property
    def connected(self) -> bool:
        """True, если оба датчика ответили на последнем тике."""
        return self._mpu_ok and self._max_ok

    def current(self) -> Reading:
        """Живые значения на момент запроса; пульс None, если датчик молчит."""
        heart_rate = self._hr.heart_rate if self._max_ok else None
        return Reading(heart_rate, self._steps.steps, self._now_utc())

    def history(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[Reading]:
        """Точки истории с включёнными границами; без границ — весь буфер."""
        return [
            r
            for r in self._history
            if (start is None or r.timestamp >= start)
            and (end is None or r.timestamp <= end)
        ]

    def tick(self) -> None:
        """Один шаг опроса. Собственный порядок: инициализация, MPU, MAX30102,
        запись истории. Сбои шины (`OSError`) не пробрасываются."""
        self._tick_mpu()
        self._tick_max()
        self._record_history()

    async def run(self, sleep: Callable[[float], Any] = asyncio.sleep) -> None:
        """Тики каждые 1 / sample_rate_hz по расписанию Clock без накопления дрейфа.

        `sleep` внедряется для тестов. Любое исключение тика (не только OSError)
        логируется, датчики помечаются сбойными, цикл продолжается.
        """
        period = 1.0 / self.config.sample_rate_hz
        next_at = self._clock.now()
        while True:
            # tick() делает блокирующий I2C прямо в цикле событий: допустимо, т.к.
            # транзакция короче миллисекунды; замер на реальной плате — PI-10.
            try:
                self.tick()
            except Exception:
                logger.exception("Сбой тика опроса; датчики помечены недоступными")
                self._mark_failed()
            next_at += period
            delay = next_at - self._clock.now()
            if delay < 0:
                # Отстали: не догоняем серией тиков, начинаем расписание заново.
                next_at = self._clock.now()
                delay = 0.0
            await sleep(delay)

    # --- внутреннее -----------------------------------------------------

    def _mark_failed(self) -> None:
        self._mpu_ok = self._max_ok = False
        self._mpu_ready = self._max_ready = False
        self._hr.reset()

    def _now_utc(self) -> datetime:
        # Метка без долей секунды: формат API `...T12:00:00Z`.
        return self._utc_now().replace(microsecond=0)

    def _tick_mpu(self) -> None:
        try:
            if not self._mpu_ready:
                self._mpu.wake()
                self._mpu_ready = True
            self._steps.update(self._mpu.read_acceleration_g())
            self._mpu_ok = True
        except OSError:
            self._mpu_ok = False
            self._mpu_ready = False  # после сбоя чип могли переподать — будим заново

    def _tick_max(self) -> None:
        try:
            if not self._max_ready:
                self._max.initialize()
                self._max_ready = True
            count = self._max.available_samples()
            if count > 0:
                for _red, ir in self._max.read_fifo_samples(count):
                    self._hr.update(ir)
            self._max_ok = True
        except OSError:
            self._max_ok = False
            self._max_ready = False
            self._hr.reset()  # окно со старыми отсчётами после сбоя недостоверно

    def _record_history(self) -> None:
        now = self._clock.now()
        if (
            self._last_history_at is not None
            and now - self._last_history_at < HISTORY_INTERVAL_S
        ):
            return
        self._last_history_at = now
        self._history.append(self.current())
