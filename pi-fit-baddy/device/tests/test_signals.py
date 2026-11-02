"""Тесты device/virtual/signals.py: accel_samples и ppg_samples.

Счётчик пиков/пересечений здесь — простой локальный помощник теста (порог +
минимальный интервал, в духе `docs/pi.md` §7), а не полноценный алгоритм
PI-06/PI-07, который этой задаче не принадлежит.
"""

import math

from device.clock import ManualClock
from device.virtual.scenarios import Segment, resolve_scenario
from device.virtual.signals import accel_samples, ppg_samples

_SAMPLE_RATE_HZ = 50.0

# Совпадают со стартовыми дефолтами device/config.py (STEP_THRESHOLD_G,
# STEP_MIN_INTERVAL_MS) просто как разумные значения для локального
# помощника теста — сам Config здесь не импортируется (не его задача, PI-06).
# Это намеренно независимая локальная копия текущих дефолтов, а не ссылка на
# них: PI-04 не трогает device/config.py (PI-01), поэтому если дефолты там
# позже изменятся, эти константы не обновятся автоматически — разойдутся,
# и это ожидаемо, не баг.
_STEP_THRESHOLD_G = 0.15
_STEP_MIN_INTERVAL_MS = 300.0


def _count_step_peaks(samples, sample_rate_hz: float) -> int:
    """Считает пики модуля вектора ускорения выше порога с минимальным
    интервалом между ними — модуль вектора минус гравитация, как в
    `docs/pi.md` §7."""
    min_interval_samples = max(1, round(_STEP_MIN_INTERVAL_MS / 1000.0 * sample_rate_hz))
    peaks = 0
    samples_since_peak = min_interval_samples
    was_above = False
    for x, y, z in samples:
        magnitude = math.sqrt(x * x + y * y + z * z) - 1.0
        is_above = magnitude > _STEP_THRESHOLD_G
        samples_since_peak += 1
        if is_above and not was_above and samples_since_peak >= min_interval_samples:
            peaks += 1
            samples_since_peak = 0
        was_above = is_above
    return peaks


def _count_mean_crossing_frequency_hz(values, sample_rate_hz: float) -> float:
    """Частота доминирующей периодики по числу пересечений среднего."""
    mean = sum(values) / len(values)
    crossings = 0
    previous_sign_positive = None
    for value in values:
        sign_positive = value > mean
        if previous_sign_positive is not None and sign_positive != previous_sign_positive:
            crossings += 1
        previous_sign_positive = sign_positive
    duration_s = len(values) / sample_rate_hz
    return (crossings / 2.0) / duration_s


def test_walk_scenario_produces_100_peaks_within_5_percent():
    # DoD PI-04: сценарий walk на 60 с при 100 шаг/мин -> ~100 пиков.
    walk = resolve_scenario("walk")

    samples = list(accel_samples(walk, _SAMPLE_RATE_HZ))
    peaks = _count_step_peaks(samples, _SAMPLE_RATE_HZ)

    expected = 100
    assert abs(peaks - expected) <= expected * 0.05


def test_rest_scenario_produces_no_detectable_peaks():
    rest = resolve_scenario("rest")

    samples = list(accel_samples(rest, _SAMPLE_RATE_HZ))
    peaks = _count_step_peaks(samples, _SAMPLE_RATE_HZ)

    assert peaks == 0


def test_run_scenario_produces_peaks_at_higher_frequency_than_walk():
    walk = resolve_scenario("walk")
    run = resolve_scenario("run")

    walk_peaks = _count_step_peaks(list(accel_samples(walk, _SAMPLE_RATE_HZ)), _SAMPLE_RATE_HZ)
    run_peaks = _count_step_peaks(list(accel_samples(run, _SAMPLE_RATE_HZ)), _SAMPLE_RATE_HZ)

    assert run_peaks > walk_peaks


def test_accel_samples_accepts_injected_clock_without_sleeping():
    walk = resolve_scenario("walk")
    clock = ManualClock(start=5.0)

    samples = list(accel_samples(walk, _SAMPLE_RATE_HZ, clock=clock))

    # Генератор не продвигает часы сам (нет time.sleep) и не блокируется.
    assert clock.now() == 5.0
    assert len(samples) == round(walk.duration_s * _SAMPLE_RATE_HZ)


def test_accel_samples_yields_expected_sample_count():
    segment = Segment(duration_s=2.0, steps_per_minute=0.0, heart_rate_bpm=70.0, noise_level=0.0)

    samples = list(accel_samples(segment, _SAMPLE_RATE_HZ))

    assert len(samples) == round(2.0 * _SAMPLE_RATE_HZ)


def test_ppg_samples_dominant_frequency_matches_heart_rate():
    segment = Segment(duration_s=30.0, steps_per_minute=0.0, heart_rate_bpm=72.0, noise_level=0.03)

    samples = list(ppg_samples(segment, _SAMPLE_RATE_HZ))
    ir_values = [ir for ir, _red in samples]

    frequency_hz = _count_mean_crossing_frequency_hz(ir_values, _SAMPLE_RATE_HZ)
    expected_hz = 72.0 / 60.0

    assert abs(frequency_hz - expected_hz) <= expected_hz * 0.15


def test_ppg_samples_are_integers_above_dc_noise_floor():
    segment = Segment(duration_s=5.0, steps_per_minute=0.0, heart_rate_bpm=80.0, noise_level=0.02)

    samples = list(ppg_samples(segment, _SAMPLE_RATE_HZ))

    assert len(samples) == round(5.0 * _SAMPLE_RATE_HZ)
    for ir, red in samples:
        assert isinstance(ir, int)
        assert isinstance(red, int)
        assert ir > 0
        assert red > 0
