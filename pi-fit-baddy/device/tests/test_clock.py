"""Тесты device/clock.py: ManualClock и MonotonicClock."""

import pytest

import device.clock as clock_module
from device.clock import ManualClock, MonotonicClock


def test_manual_clock_starts_at_given_value():
    clock = ManualClock(start=10.0)

    assert clock.now() == 10.0


def test_manual_clock_advance_moves_now_without_real_wait():
    clock = ManualClock(start=10.0)

    clock.advance(5.0)

    assert clock.now() == 15.0

    clock.advance(0.5)

    assert clock.now() == 15.5


def test_manual_clock_rejects_negative_advance():
    clock = ManualClock()

    with pytest.raises(ValueError):
        clock.advance(-1.0)


def test_monotonic_clock_delegates_to_time_monotonic(monkeypatch):
    monkeypatch.setattr(clock_module.time, "monotonic", lambda: 42.0)

    clock = MonotonicClock()

    assert clock.now() == 42.0
