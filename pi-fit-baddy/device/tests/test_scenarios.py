"""Тесты device/virtual/scenarios.py: реестр встроенных сценариев."""

import pytest

from device.virtual.scenarios import SCENARIOS, Segment, resolve_scenario


@pytest.mark.parametrize("name", ["rest", "walk", "run", "recovery"])
def test_resolve_scenario_returns_segment_for_known_name(name):
    segment = resolve_scenario(name)

    assert isinstance(segment, Segment)
    assert segment is SCENARIOS[name]


def test_walk_scenario_matches_dod_test_parameters():
    # DoD PI-04: сценарий walk на 60 с при 100 шаг/мин.
    walk = resolve_scenario("walk")

    assert walk.duration_s == 60.0
    assert walk.steps_per_minute == 100.0


def test_rest_scenario_has_no_steps():
    rest = resolve_scenario("rest")

    assert rest.steps_per_minute == 0.0


def test_run_scenario_has_higher_cadence_than_walk():
    walk = resolve_scenario("walk")
    run = resolve_scenario("run")

    assert run.steps_per_minute > walk.steps_per_minute
    assert run.heart_rate_bpm > walk.heart_rate_bpm


def test_resolve_scenario_raises_clear_error_for_unknown_name():
    with pytest.raises(ValueError, match="data/walk_2026-10-14"):
        resolve_scenario("data/walk_2026-10-14")
