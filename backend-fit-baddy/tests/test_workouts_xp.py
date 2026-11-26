"""WKT-09 — XP за тренировку определяет модуль питомца, workouts его только хранит."""
import inspect
from datetime import datetime, timezone

from app.modules.workouts import service as workouts_service
from tests.conftest import auth_header, complete_workout, register_user


def at(day: int) -> datetime:
    return datetime(2026, 10, day, 18, 0, tzinfo=timezone.utc)


def test_workouts_module_has_no_xp_constants():
    source = inspect.getsource(workouts_service)
    assert "= 25" not in source
    assert not [name for name in dir(workouts_service) if name.startswith("XP")]


def test_xp_awarded_follows_pet_streak_rules(client, monkeypatch):
    token, _ = register_user(client)
    headers = auth_header(token)

    awarded = []
    for day in (1, 2, 3):
        monkeypatch.setattr(workouts_service, "utc_now", lambda d=day: at(d))
        awarded.append(complete_workout(client, headers)["xp_awarded"])

    assert awarded == [25, 30, 35]  # 25 + 5 * (streak - 1), правила D-13


def test_xp_awarded_after_streak_break_is_base(client, monkeypatch):
    token, _ = register_user(client)
    headers = auth_header(token)

    monkeypatch.setattr(workouts_service, "utc_now", lambda: at(1))
    complete_workout(client, headers)
    monkeypatch.setattr(workouts_service, "utc_now", lambda: at(9))
    assert complete_workout(client, headers)["xp_awarded"] == 25


def test_history_shows_stored_xp_awarded(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    done = complete_workout(client, headers)
    items = client.get("/api/v1/workouts/history", headers=headers).json()["items"]
    assert items[0]["xp_awarded"] == done["xp_awarded"] > 0