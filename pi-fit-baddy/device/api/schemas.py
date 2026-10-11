"""Схемы ответов `docs/pi.md` §5: ровно поля контракта, без лишних."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from device.services.sampler import Reading


class StatusOut(BaseModel):
    connected: bool
    battery: int
    mode: str


class VitalsOut(BaseModel):
    heart_rate: int | None
    steps: int
    timestamp: str


def format_timestamp(value: datetime) -> str:
    """ISO-8601 UTC без долей секунды: `2026-10-14T12:00:00Z`."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vitals_out(reading: Reading) -> VitalsOut:
    return VitalsOut(
        heart_rate=reading.heart_rate,
        steps=reading.steps,
        timestamp=format_timestamp(reading.timestamp),
    )
