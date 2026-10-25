"""Схемы ответов `docs/pi.md` §5: ровно поля контракта, без лишних."""

from __future__ import annotations

from pydantic import BaseModel

from device.services.sampler import Reading
from device.timefmt import format_timestamp


class StatusOut(BaseModel):
    connected: bool
    battery: int
    mode: str


class VitalsOut(BaseModel):
    heart_rate: int | None
    steps: int
    timestamp: str


def vitals_out(reading: Reading) -> VitalsOut:
    return VitalsOut(
        heart_rate=reading.heart_rate,
        steps=reading.steps,
        timestamp=format_timestamp(reading.timestamp),
    )
