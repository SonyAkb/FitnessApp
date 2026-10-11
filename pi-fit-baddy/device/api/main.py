"""Локальный API узла Pi по контракту `docs/pi.md` §5.

Запуск: `SENSOR_MODE=mock uvicorn device.api.main:app --port 8080`.
Импорт модуля ничего не собирает: Sampler строится в `lifespan`.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from device.api.schemas import StatusOut, VitalsOut, vitals_out
from device.config import Config, load_config
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
    run_loop: bool = True,
    # Собственное решение: интервал стрима по умолчанию 1 с (контракт: 1–2 с).
    stream_interval_s: float = 1.0,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active = sampler or Sampler.from_config(config or load_config())
        app.state.sampler = active
        active.tick()  # первый ответ не должен быть до первого опроса
        task = asyncio.create_task(active.run()) if run_loop else None
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task

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
