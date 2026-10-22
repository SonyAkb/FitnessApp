"""Тесты StepCounter (PI-06): потоковый подсчёт шагов."""

from __future__ import annotations

import random

import pytest

from device.bus.fake_smbus import FakeSMBus
from device.clock import ManualClock
from device.config import load_config
from device.drivers.mpu6050 import Mpu6050
from device.services.step_counter import StepCounter
from device.virtual.mpu6050 import VirtualMPU6050
from device.virtual.scenarios import resolve_scenario
from device.virtual.signals import accel_samples

RATE = 50.0
DT = 1.0 / RATE


def _counter(clock: ManualClock, **kw) -> StepCounter:
    params = {"threshold_g": 0.15, "min_interval_ms": 300, "smoothing_samples": 3}
    params.update(kw)
    return StepCounter(clock, **params)


def _feed(counter: StepCounter, clock: ManualClock, samples) -> int:
    for s in samples:
        clock.advance(DT)
        counter.update(s)
    return counter.steps


def _scenario(name: str, seed: int = 1):
    random.seed(seed)
    return list(accel_samples(resolve_scenario(name), RATE))


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
@pytest.mark.parametrize(
    "name,expected,tol",
    [("walk", 100, 5), ("run", 160, 8), ("recovery", 20, 1), ("rest", 0, 0)],
)
def test_scenarios(name, expected, tol, seed):
    clock = ManualClock()
    counter = _counter(clock)
    steps = _feed(counter, clock, _scenario(name, seed))
    assert abs(steps - expected) <= tol


def test_state_kept_between_calls_one_by_one_and_in_chunks():
    samples = _scenario("walk", seed=7)

    clock1 = ManualClock()
    c1 = _counter(clock1)
    _feed(c1, clock1, samples)

    clock2 = ManualClock()
    c2 = _counter(clock2)
    for i in range(0, len(samples), 37):
        _feed(c2, clock2, samples[i : i + 37])

    assert c1.steps == c2.steps > 0


def _pulses(indices: list[int], total: int, amp: float):
    values = [0.0] * total
    for i in indices:
        values[i] = amp
    return [(1.0 + v, 0.0, 0.0) for v in values]


def test_two_bursts_closer_than_min_interval_count_once():
    clock = ManualClock()
    counter = _counter(clock)
    # импульсы через 4 отсчёта = 80 мс < 300 мс
    assert _feed(counter, clock, _pulses([10, 14], 40, 0.9)) == 1


def test_two_bursts_farther_than_min_interval_count_twice():
    clock = ManualClock()
    counter = _counter(clock)
    # через 20 отсчётов = 400 мс > 300 мс
    assert _feed(counter, clock, _pulses([10, 30], 60, 0.9)) == 2


def test_weak_burst_below_threshold_not_counted():
    clock = ManualClock()
    counter = _counter(clock)
    # после усреднения по 3 отсчётам: 0.3 / 3 = 0.1 g < 0.15 g
    assert _feed(counter, clock, _pulses([10], 40, 0.3)) == 0


def test_orientation_independent():
    samples = _scenario("walk", seed=3)
    swapped = [(z, y, x) for x, y, z in samples]  # гравитация и всплеск на оси Z

    clock1 = ManualClock()
    c1 = _counter(clock1)
    _feed(c1, clock1, samples)
    clock2 = ManualClock()
    c2 = _counter(clock2)
    _feed(c2, clock2, swapped)

    assert c1.steps == c2.steps > 0


def test_full_stack_through_driver():
    random.seed(5)
    bus = FakeSMBus()
    bus.register_device(0x68, VirtualMPU6050(accel_samples(resolve_scenario("walk"), RATE)))
    driver = Mpu6050(bus, 0x68)
    driver.wake()
    clock = ManualClock()
    counter = _counter(clock)
    for _ in range(int(60 * RATE)):
        clock.advance(DT)
        counter.update(driver.read_acceleration_g())
    assert 95 <= counter.steps <= 105


def test_reset_clears_state():
    clock = ManualClock()
    counter = _counter(clock)
    _feed(counter, clock, _pulses([10], 40, 0.9))
    assert counter.steps == 1
    counter.reset()
    assert counter.steps == 0
    assert _feed(counter, clock, _pulses([10], 40, 0.9)) == 1


@pytest.fixture(autouse=True)
def _clean_step_env(monkeypatch):
    for name in ("STEP_THRESHOLD_G", "STEP_MIN_INTERVAL_MS", "STEP_SMOOTHING_SAMPLES"):
        monkeypatch.delenv(name, raising=False)


def _from_config(clock: ManualClock) -> StepCounter:
    return StepCounter.from_config(load_config(), clock)


def test_from_config_threshold(monkeypatch):
    monkeypatch.setenv("STEP_THRESHOLD_G", "5")
    clock = ManualClock()
    # порог 5 g — обычный всплеск не засчитывается
    assert _feed(_from_config(clock), clock, _pulses([10], 40, 0.9)) == 0


def test_from_config_smoothing_samples(monkeypatch):
    weak = _pulses([10], 40, 0.3)
    clock = ManualClock()
    # по умолчанию окно 3: 0.3 / 3 = 0.1 g < порога, шага нет
    assert _feed(_from_config(clock), clock, weak) == 0

    monkeypatch.setenv("STEP_SMOOTHING_SAMPLES", "1")
    clock = ManualClock()
    # окно 1: всплеск 0.3 g не размывается и засчитывается
    assert _feed(_from_config(clock), clock, weak) == 1


def test_from_config_min_interval(monkeypatch):
    pair = _pulses([10, 30], 60, 0.9)  # 400 мс между всплесками
    clock = ManualClock()
    assert _feed(_from_config(clock), clock, pair) == 2

    monkeypatch.setenv("STEP_MIN_INTERVAL_MS", "1000")
    clock = ManualClock()
    assert _feed(_from_config(clock), clock, pair) == 1


def _levels(values):
    return [(1.0 + v, 0.0, 0.0) for v in values]


def test_long_burst_with_ripple_counts_once():
    clock = ManualClock()
    counter = _counter(clock, smoothing_samples=1)
    # всплеск ~1 с с рябью: два локальных максимума на расстоянии > 300 мс,
    # оба выше порога, сигнал между ними не опускается до порога
    values = [0.0] * 5 + [0.3] + [0.5] * 20 + [0.3] * 5 + [0.5] * 20 + [0.3, 0.0] + [0.0] * 10
    assert _feed(counter, clock, _levels(values)) == 1


def test_second_burst_after_drop_below_threshold_counts_again():
    clock = ManualClock()
    counter = _counter(clock, smoothing_samples=1)
    burst = [0.3, 0.5, 0.3]
    values = [0.0] * 5 + burst + [0.1] * 20 + burst + [0.0] * 5
    assert _feed(counter, clock, _levels(values)) == 2


@pytest.mark.parametrize("window", [1, 3, 5])
def test_clean_pulse_train_for_different_windows(window):
    clock = ManualClock()
    counter = _counter(clock, smoothing_samples=window)
    values = [0.0] * 5
    for _ in range(6):
        values += [0.9] * 3 + [0.0] * 22  # 500 мс между всплесками
    assert _feed(counter, clock, _levels(values)) == 6


def test_interval_boundary():
    # при 50 Гц 15 отсчётов = ровно 300 мс = STEP_MIN_INTERVAL_MS
    exact = _pulses([10, 25], 50, 0.9)
    clock = ManualClock()
    assert _feed(_counter(clock, smoothing_samples=1), clock, exact) == 2

    below = _pulses([10, 24], 50, 0.9)  # 280 мс
    clock = ManualClock()
    assert _feed(_counter(clock, smoothing_samples=1), clock, below) == 1


def test_invalid_smoothing_rejected():
    with pytest.raises(ValueError):
        _counter(ManualClock(), smoothing_samples=0)
