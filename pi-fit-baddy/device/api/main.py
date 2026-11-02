"""Локальный API узла Pi по контракту `docs/pi.md` §5.

Запуск: `SENSOR_MODE=mock uvicorn device.api.main:app --port 8080`.
Импорт модуля ничего не собирает: Sampler строится в `lifespan`.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from device.api.schemas import StatusOut, VitalsOut, vitals_out
from device.config import Config, load_config
from device.services.pairing import resolve_credentials
from device.services.publisher import HTTP_TIMEOUT_S, Publisher
from device.services.sampler import Sampler


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


# Обработчики намеренно `async def`: они выполняются в потоке цикла событий,
# как и Sampler.run(), поэтому гонок с буфером истории нет.
def create_app(
    config: Config | None = None,
    *,
    sampler: Sampler | None = None,
    publisher: Publisher | None = None,
    run_loop: bool = True,
    # Собственное решение: интервал стрима по умолчанию 1 с (контракт: 1–2 с).
    stream_interval_s: float = 1.0,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        cfg = config or (sampler.config if sampler else load_config())
        active = sampler or Sampler.from_config(cfg)
        app.state.sampler = active
        active.tick()  # первый ответ не должен быть до первого опроса
        client: httpx.AsyncClient | None = None
        active_publisher = publisher
        if run_loop and active_publisher is None and cfg.publish_enabled:
            client = httpx.AsyncClient(timeout=HTTP_TIMEOUT_S)
            try:
                credentials = await resolve_credentials(cfg, client)
                active_publisher = Publisher.from_config(
                    cfg,
                    active,
                    client,
                    device_id=credentials.device_id if credentials else None,
                    device_token=credentials.device_token if credentials else None,
                )
            except ValueError:
                await client.aclose()
                raise
        app.state.publisher = active_publisher
        tasks: list[asyncio.Task[None]] = []
        if run_loop:
            tasks.append(asyncio.create_task(active.run()))
            if active_publisher is not None:
                tasks.append(asyncio.create_task(active_publisher.run()))
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            for task in tasks:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task
            if client is not None:
                await client.aclose()

    app = FastAPI(title="FitQuest Pi node", lifespan=lifespan)

    @app.get("/device/status", response_model=StatusOut)
    async def status(request: Request) -> StatusOut:
        active: Sampler = request.app.state.sampler
        return StatusOut(
            connected=active.connected,
            battery=active.config.battery_percent,
            mode=active.config.sensor_mode,
        )

    @app.get("/device/vitals/current", response_model=VitalsOut)
    async def current(request: Request) -> VitalsOut:
        return vitals_out(request.app.state.sampler.current())

    @app.get("/device/vitals/history", response_model=list[VitalsOut])
    async def history(
        request: Request,
        from_: datetime | None = Query(None, alias="from"),
        to: datetime | None = None,
    ) -> list[VitalsOut]:
        points = request.app.state.sampler.history(_as_utc(from_), _as_utc(to))
        return [vitals_out(p) for p in points]

    @app.websocket("/device/stream")
    async def stream(websocket: WebSocket) -> None:
        await websocket.accept()
        active: Sampler = websocket.app.state.sampler
        try:
            while True:
                await websocket.send_json(vitals_out(active.current()).model_dump())
                await asyncio.sleep(stream_interval_s)
        except (WebSocketDisconnect, RuntimeError):  # клиент отключился
            pass

    return app


app = create_app()
