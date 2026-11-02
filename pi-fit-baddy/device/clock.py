"""Источник времени для узла Pi.

Вся тестируемая логика (счётчик шагов, оценка пульса, виртуальные чипы,
sampler) получает время только через `Clock`, а не напрямую через
`time.monotonic`/`time.sleep` — это убирает недетерминизм из тестов
(docs/pi.md §3.6). В рантайме используется `MonotonicClock`, в тестах —
`ManualClock` с управляемым сдвигом.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod


class Clock(ABC):
    """Абстракция источника времени."""

    @abstractmethod
    def now(self) -> float:
        """Текущее время в секундах по монотонной шкале."""
        raise NotImplementedError


class MonotonicClock(Clock):
    """Реальные часы на `time.monotonic()` — используются в рантайме."""

    def now(self) -> float:
        return time.monotonic()


class ManualClock(Clock):
    """Управляемые часы для тестов: время двигается только через `advance()`."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        """Сдвигает часы вперёд на `seconds` без реального ожидания."""
        if seconds < 0:
            raise ValueError("ManualClock не может идти назад")
        self._now += seconds
