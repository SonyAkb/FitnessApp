"""Общее форматирование времени узла Pi (используется api и services)."""

from __future__ import annotations

from datetime import datetime, timezone


def format_timestamp(value: datetime) -> str:
    """ISO-8601 UTC без долей секунды: `2026-10-14T12:00:00Z`."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
