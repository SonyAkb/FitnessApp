"""Тесты device/services/sampler.py: tick с ManualClock, история, сбои шины."""

import dataclasses
from datetime import datetime, timedelta, timezone

from device.bus.factory import create_bus
from device.clock import ManualClock
from device.config import load_config
from device.services.sampler import Sampler

T0 = datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)


class Env:
    """Sampler на mock-шине; время UTC выводится из ManualClock."""

    def __init__(self, **overrides):
        self.config = dataclasses.replace(
            load_config(), sensor_mode="mock", scenario="walk", **overrides
        )
        self.clock = ManualClock()
        self.bus = create_bus(self.config)
        self.sampler = Sampler(
            self.config,
            self.bus,
            self.clock,
            utc_now=lambda: T0 + timedelta(seconds=self.clock.now()),
        )

    def run(self, seconds):
        period = 1.0 / self.config.sample_rate_hz
        for _ in range(round(seconds * self.config.sample_rate_hz)):
            self.sampler.tick()
            self.clock.advance(period)


def test_walk_gives_steps_and_heart_rate():
    env = Env()
    env.run(1.0)
    assert env.sampler.current().heart_rate is None  # окно ещё не накоплено

    env.run(19.0)
    reading = env.sampler.current()

    assert env.sampler.connected is True
    assert 25 <= reading.steps <= 40  # ~100 шаг/мин за 20 с
    assert reading.heart_rate is not None and abs(reading.heart_rate - 95) <= 5


def test_signal_loops_after_scenario_end():
    env = Env()
    env.run(70.0)  # walk идёт 60 с
    steps_before = env.sampler.current().steps

    env.run(20.0)
    reading = env.sampler.current()

    assert reading.steps > steps_before
    assert reading.heart_rate is not None and abs(reading.heart_rate - 95) <= 5


def test_history_once_per_second_with_bounds():
    env = Env()
    env.run(10.0)

    points = env.sampler.history()
    assert len(points) == 10
    assert [p.timestamp for p in points] == [T0 + timedelta(seconds=i) for i in range(10)]

    sub = env.sampler.history(T0 + timedelta(seconds=3), T0 + timedelta(seconds=5))
    assert [p.timestamp for p in sub] == [T0 + timedelta(seconds=i) for i in (3, 4, 5)]


def test_history_evicts_oldest():
    env = Env(history_max_points=5, sample_rate_hz=10.0)
    env.run(12.0)

    points = env.sampler.history()
    assert len(points) == 5
    assert points[0].timestamp == T0 + timedelta(seconds=7)


def test_bus_failure_and_recovery():
    env = Env()
    env.run(2.0)
    assert env.sampler.connected is True

    devices = dict(env.bus._devices)  # noqa: SLF001 - имитируем отключение чипов
    env.bus._devices.clear()  # noqa: SLF001
    env.run(0.1)
    assert env.sampler.connected is False
    assert env.sampler.current().heart_rate is None

    env.bus._devices.update(devices)  # noqa: SLF001
    env.run(0.2)
    assert env.sampler.connected is True


def test_init_failure_is_retried():
    env = Env()
    devices = dict(env.bus._devices)  # noqa: SLF001
    env.bus._devices.clear()  # noqa: SLF001

    env.run(0.5)
    assert env.sampler.connected is False

    env.bus._devices.update(devices)  # noqa: SLF001
    env.run(1.0)
    assert env.sampler.connected is True
    assert env.sampler.current().steps >= 0


def test_from_config_smoke_in_mock_mode():
    config = dataclasses.replace(load_config(), sensor_mode="mock", scenario="walk")
    clock = ManualClock()
    sampler = Sampler.from_config(config, clock, lambda: T0)

    for _ in range(50):
        sampler.tick()
        clock.advance(0.02)

    assert sampler.connected is True
    assert sampler.current().timestamp == T0


def _run_with_fake_sleep(env, ticks, on_sleep=None):
    """Гоняет Sampler.run(): fake sleep двигает ManualClock; после `ticks` сна — стоп."""
    import asyncio

    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)
        if on_sleep:
            on_sleep(len(sleeps))
        env.clock.advance(delay)
        if len(sleeps) >= ticks:
            raise asyncio.CancelledError

    try:
        asyncio.run(env.sampler.run(fake_sleep))
    except asyncio.CancelledError:
        pass
    return sleeps


def test_run_follows_schedule_without_drift():
    env = Env()
    ticks_at = []
    original = env.sampler.tick

    def spy():
        ticks_at.append(env.clock.now())
        original()
        env.clock.advance(0.005)  # тик «стоит» 5 мс

    env.sampler.tick = spy
    sleeps = _run_with_fake_sleep(env, 5)

    assert all(abs(b - a - 0.02) < 1e-9 for a, b in zip(ticks_at, ticks_at[1:]))
    assert all(abs(d - 0.015) < 1e-9 for d in sleeps)  # 0.02 минус время тика


def test_run_does_not_replay_after_stall():
    env = Env()
    ticks_at = []
    original = env.sampler.tick
    env.sampler.tick = lambda: (ticks_at.append(env.clock.now()), original())

    def stall(n):
        if n == 2:
            env.clock.advance(10.0)  # длинная пауза

    sleeps = _run_with_fake_sleep(env, 5, on_sleep=stall)

    assert sleeps[2] == 0.0  # отстали -> без догоняющей серии
    assert len(ticks_at) == 5  # пропущенные ~500 тиков не проигрываются
    assert abs(sleeps[3] - 0.02) < 1e-9  # расписание сброшено и снова ровное


def test_run_survives_unexpected_exception():
    env = Env()
    original = env.sampler._mpu.read_acceleration_g  # noqa: SLF001
    calls = {"n": 0}
    states = []

    def flaky():
        calls["n"] += 1
        if calls["n"] == 3:
            raise ValueError("boom")
        return original()

    env.sampler._mpu.read_acceleration_g = flaky  # noqa: SLF001
    _run_with_fake_sleep(env, 6, on_sleep=lambda n: states.append(env.sampler.connected))

    assert states[:2] == [True, True]
    assert states[2] is False
    assert states[3] is True
