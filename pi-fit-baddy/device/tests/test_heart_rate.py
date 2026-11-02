"""Тесты HeartRateEstimator (PI-07): потоковая оценка ЧСС по ИК-каналу."""

from __future__ import annotations

import math
import random

import pytest

from device.bus.fake_smbus import FakeSMBus
from device.clock import ManualClock
from device.config import load_config
from device.drivers.max30102 import Max30102
from device.services.heart_rate import HeartRateEstimator
from device.virtual.max30102 import VirtualMax30102
from device.virtual.scenarios import Segment, resolve_scenario
from device.virtual.signals import ppg_samples

RATE = 50.0
DT = 1.0 / RATE
SEEDS = [1, 2, 3, 4, 5]


def _estimator(clock: ManualClock, **kw) -> HeartRateEstimator:
    params = {
        "band_low_hz": 0.5,
        "band_high_hz": 4.0,
        "window_s": 5.0,
        "min_signal_ratio": 0.01,
    }
    params.update(kw)
    return HeartRateEstimator(clock, **params)


def _feed(est: HeartRateEstimator, clock: ManualClock, irs, dt: float = DT):
    result = None
    for ir in irs:
        clock.advance(dt)
        result = est.update(ir)
    return result


def _ir(segment: Segment, seed: int) -> list[int]:
    random.seed(seed)
    return [ir for ir, _red in ppg_samples(segment, RATE)]


def _segment(bpm: float, duration_s: float = 15.0, noise: float = 0.03) -> Segment:
    return Segment(
        duration_s=duration_s, steps_per_minute=0.0, heart_rate_bpm=bpm, noise_level=noise
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_clean_72_bpm(seed):
    clock = ManualClock()
    est = _estimator(clock)
    result = _feed(est, clock, _ir(_segment(72.0, 12.0), seed))
    assert result is not None and abs(result - 72) <= 3
    assert est.heart_rate == result


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name,tol", [("rest", 3), ("walk", 3), ("recovery", 3), ("run", 5)])
def test_scenarios(name, tol, seed):
    base = resolve_scenario(name)
    segment = _segment(base.heart_rate_bpm, 15.0, base.noise_level)
    clock = ManualClock()
    est = _estimator(clock)
    result = _feed(est, clock, _ir(segment, seed))
    assert result is not None
    assert abs(result - base.heart_rate_bpm) <= tol


@pytest.mark.parametrize("seed", SEEDS)
def test_weak_signal_returns_none(seed):
    # Амплитуда пульса 100 при DC 50000 = 0.2 %.
    rng = random.Random(seed)
    irs = [
        round(50_000 + 100 * math.sin(2 * math.pi * 1.2 * i * DT) + rng.uniform(-5, 5))
        for i in range(750)
    ]
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, irs) is None


def test_weak_threshold_comes_from_parameter():
    irs = [round(50_000 + 100 * math.sin(2 * math.pi * 1.2 * i * DT)) for i in range(750)]
    clock = ManualClock()
    assert _feed(_estimator(clock), clock, irs) is None
    clock2 = ManualClock()
    result = _feed(_estimator(clock2, min_signal_ratio=0.001), clock2, irs)
    assert result is not None and abs(result - 72) <= 3


def test_constant_level_returns_none():
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, [50_000] * 750) is None


@pytest.mark.parametrize("seed", range(1, 31))
def test_noise_without_pulse_returns_none(seed):
    rng = random.Random(seed)
    irs = [50_000 + rng.uniform(-3000, 3000) for _ in range(1000)]
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, irs) is None


def test_irregular_beats_return_none():
    # Интервалы чередуются 0.5 с и 1.5 с (отношение 1/3 < 0.5).
    irs: list[float] = []
    beat = 0
    while len(irs) < 1000:
        n = int((0.5 if beat % 2 == 0 else 1.5) * RATE)
        irs.extend(50_000 + 2000 * math.sin(2 * math.pi * k / n) for k in range(n))
        beat += 1
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, irs) is None


def test_window_accumulates_then_number():
    clock = ManualClock()
    est = _estimator(clock)
    irs = _ir(_segment(72.0, 12.0), 1)
    split = int(3 * RATE)
    for ir in irs[:split]:
        clock.advance(DT)
        assert est.update(ir) is None
    assert _feed(est, clock, irs[split:]) is not None


def test_no_sensor_signal_dc_not_positive():
    clock = ManualClock()
    est = _estimator(clock)
    irs = [-1000 + 2000 * math.sin(2 * math.pi * 1.2 * i * DT) for i in range(750)]
    assert _feed(est, clock, irs) is None
    clock2 = ManualClock()
    est2 = _estimator(clock2)
    assert _feed(est2, clock2, [0] * 750) is None


def test_one_by_one_equals_chunks():
    irs = _ir(_segment(72.0, 12.0), 7)

    clock1 = ManualClock()
    e1 = _estimator(clock1)
    r1 = _feed(e1, clock1, irs)

    clock2 = ManualClock()
    e2 = _estimator(clock2)
    r2 = None
    for start in range(0, len(irs), 37):
        r2 = _feed(e2, clock2, irs[start : start + 37])
    assert r1 == r2 and r1 is not None


@pytest.mark.parametrize("seed", SEEDS)
def test_jittered_timestamps(seed):
    irs = _ir(_segment(72.0, 15.0), seed)
    rng = random.Random(seed + 100)
    clock = ManualClock()
    est = _estimator(clock)
    result = None
    for ir in irs:
        clock.advance(DT * rng.uniform(0.8, 1.2))
        result = est.update(ir)
    assert result is not None and abs(result - 72) <= 3


def test_non_advancing_time_skips_sample():
    clock = ManualClock()
    est = _estimator(clock)
    result = _feed(est, clock, _ir(_segment(72.0, 12.0), 1))
    assert result is not None
    # время не двигается: отсчёты пропускаются, оценка не меняется
    for _ in range(20):
        assert est.update(1_000_000) == result
    assert est.heart_rate == result


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_full_stack_via_driver(seed):
    random.seed(seed)
    clock = ManualClock()
    bus = FakeSMBus()
    bus.register_device(0x57, VirtualMax30102(ppg_samples(_segment(72.0, 15.0), RATE)))
    drv = Max30102(bus, 0x57)
    drv.initialize()
    est = _estimator(clock)
    result = None
    for _ in range(int(12 * RATE)):
        clock.advance(DT)
        drv.available_samples()  # на виртуальном чипе пополняет FIFO
        _red, ir = drv.read_fifo_samples(1)[0]
        result = est.update(ir)
    assert result is not None and abs(result - 72) <= 3


def test_reset():
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, _ir(_segment(72.0, 12.0), 1)) is not None
    est.reset()
    assert est.heart_rate is None
    # после сброса окно накапливается заново
    assert _feed(est, clock, _ir(_segment(72.0, 3.0), 1)) is None
    assert _feed(est, clock, _ir(_segment(72.0, 12.0), 1)) is not None


def _from_env(monkeypatch, **env):
    for name in ("HR_BAND_HZ_LOW", "HR_BAND_HZ_HIGH", "HR_WINDOW_S", "HR_MIN_SIGNAL_RATIO"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    clock = ManualClock()
    return HeartRateEstimator.from_config(load_config(), clock), clock


def test_from_config_binds_parameters(monkeypatch):
    irs = _ir(_segment(72.0, 14.0), 1)

    # контрольный прогон: с настройками по умолчанию число есть
    est, clock = _from_env(monkeypatch)
    result = _feed(est, clock, irs)
    assert result is not None and abs(result - 72) <= 3

    # каждая переменная окружения сама по себе превращает число в None
    for env in (
        {"HR_MIN_SIGNAL_RATIO": "0.5"},
        {"HR_WINDOW_S": "20"},
        {"HR_BAND_HZ_HIGH": "0.8"},
    ):
        est, clock = _from_env(monkeypatch, **env)
        assert _feed(est, clock, irs) is None, env


def test_from_config_band_low_filters_pulse(monkeypatch):
    # Простой EMA-фильтр срезает мягко, поэтому берём пульс малой амплитуды
    # (0.0125 от DC): при срезе 0.5 Гц он выше порога, при срезе 3 Гц - ниже.
    irs = [round(50_000 + 700 * math.sin(2 * math.pi * 1.2 * i * DT)) for i in range(750)]
    est, clock = _from_env(monkeypatch)
    result = _feed(est, clock, irs)
    assert result is not None and abs(result - 72) <= 3
    est, clock = _from_env(monkeypatch, HR_BAND_HZ_LOW="3.0")
    assert _feed(est, clock, irs) is None


@pytest.mark.parametrize("bpm,expect_none", [(234.0, True), (228.0, False), (72.0, False)])
def test_bpm_range_limit(bpm, expect_none):
    # Бэкенд отклоняет heart_rate вне 30-230 (docs/API_CONTRACT.md), 3.9 Гц = 234 уд/мин.
    clock = ManualClock()
    est = _estimator(clock, band_high_hz=5.0)
    seen = []
    for ir in _ir(_segment(bpm, 15.0, 0.0), 1):
        clock.advance(DT)
        v = est.update(ir)
        if v is not None:
            seen.append(v)
            assert 30 <= v <= 230
    if expect_none:
        assert not seen
    elif bpm == 72.0:
        assert seen and abs(seen[-1] - 72) <= 3


def test_follows_rate_change():
    low, high = 60.0, 120.0
    irs = _ir(_segment(low, 25.0), 1) + _ir(_segment(high, 25.0), 2)
    clock = ManualClock()
    est = _estimator(clock)
    for ir in irs:
        clock.advance(DT)
        v = est.update(ir)
        if v is not None:
            assert low - 5 <= v <= high + 5
    assert abs(est.heart_rate - 120) <= 3


def test_recovers_after_weak_signal():
    weak = [round(50_000 + 20 * math.sin(2 * math.pi * 1.2 * i * DT)) for i in range(500)]
    clock = ManualClock()
    est = _estimator(clock)
    assert _feed(est, clock, weak) is None
    result = _feed(est, clock, _ir(_segment(72.0, 12.0), 1))
    assert result is not None and abs(result - 72) <= 3


@pytest.mark.parametrize("fs,tol", [(100.0, 3), (25.0, 4)])
def test_other_sample_rates(fs, tol):
    # При 25 Гц один отсчёт 40 мс: на 72 уд/мин это до ~3 уд/мин квантования.
    random.seed(1)
    irs = [ir for ir, _ in ppg_samples(_segment(72.0, 12.0), fs)]
    clock = ManualClock()
    est = _estimator(clock)
    result = _feed(est, clock, irs, dt=1.0 / fs)
    assert result is not None and abs(result - 72) <= tol


@pytest.mark.parametrize(
    "kw",
    [
        {"band_low_hz": 4.0, "band_high_hz": 0.5},
        {"window_s": 0.0},
        {"min_signal_ratio": -0.1},
    ],
)
def test_invalid_parameters(kw):
    with pytest.raises(ValueError):
        _estimator(ManualClock(), **kw)
