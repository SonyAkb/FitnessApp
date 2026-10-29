"""PET-06 — настроение по дням без тренировки, сон и бонус возвращения (US-D2, D-14).

Часы управляемые: фиксируем `utc_now` через monkeypatch на отметку «сейчас».
Пороги D-14: 1–2 дня → neutral, 3–13 → sad, 14+ → sleeping.
Возвращение после 3+ дней: +10 XP и событие `pet_returned` → уведомление «Рад тебя видеть!».
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.database import SessionLocal
from app.events import PET_RETURNED
from app.modules.notifications import service as notification_service
from app.modules.pet import service as pet_service
from tests.conftest import auth_header, complete_workout, register_user

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def frozen_clock(monkeypatch):
    """Управляемые часы: сервис настроения берёт «сейчас» из `pet.service.utc_now`.

    Фикстура возвращает словарь-holder: меняем `holder["now"]`, чтобы перемотать
    время (например, для сценария возвращения питомца).
    """
    holder = {"now": NOW}
    monkeypatch.setattr(pet_service, "utc_now", lambda: holder["now"])
    return holder


@pytest.fixture()
def returned_events():
    """Подписка на событие `pet_returned` с гарантированной отпиской после теста."""
    events: list[dict] = []
    handler = lambda payload, db: events.append(payload)  # noqa: E731
    pet_service.event_bus.subscribe(PET_RETURNED, handler)
    try:
        yield events
    finally:
        pet_service.event_bus.unsubscribe(PET_RETURNED, handler)


def make_pet_with_last_activity(db_session, user_id: int, last: date | None):
    pet = pet_service.get_or_create_pet(db_session, user_id)
    pet.last_activity_date = last
    pet.mood = "idle"
    db_session.flush()
    return pet


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, "idle"),
        (1, "neutral"),
        (2, "neutral"),
        (3, "sad"),
        (13, "sad"),
        (14, "sleeping"),
        (30, "sleeping"),
    ],
)
def test_mood_thresholds_per_day(days, expected):
    assert pet_service.mood_for_days_without_training(days, "idle") == expected


@pytest.mark.parametrize(
    ("absence_days", "expected"),
    [(1, "neutral"), (2, "neutral"), (3, "sad"), (13, "sad"), (14, "sleeping")],
)
def test_refresh_mood_at_each_threshold(client, db_session, frozen_clock, absence_days, expected):
    _, user = register_user(client)
    last = (frozen_clock["now"] - timedelta(days=absence_days)).date()
    pet = make_pet_with_last_activity(db_session, user["id"], last)

    assert pet_service.refresh_mood(db_session, pet) == expected
    assert pet.mood == expected


def test_refresh_mood_keeps_fresh_workout_mood(client, db_session, frozen_clock):
    """0 дней без тренировки (сегодняшняя активность) — happy не перебивается."""
    _, user = register_user(client)
    pet = make_pet_with_last_activity(db_session, user["id"], frozen_clock["now"].date())
    pet.mood = "happy"

    assert pet_service.refresh_mood(db_session, pet) == "happy"


def test_new_pet_without_activity_stays_idle(client, db_session, frozen_clock):
    _, user = register_user(client)
    pet = make_pet_with_last_activity(db_session, user["id"], None)

    assert pet_service.days_since_last_activity(pet) == 0
    assert pet_service.refresh_mood(db_session, pet) == "idle"


def test_days_since_last_activity_counts_calendar_days(client, db_session, frozen_clock):
    _, user = register_user(client)
    pet = make_pet_with_last_activity(db_session, user["id"], date(2026, 10, 17))
    assert pet_service.days_since_last_activity(pet) == 3
    pet.last_activity_date = date(2026, 10, 25)
    assert pet_service.days_since_last_activity(pet) == 0


@pytest.mark.parametrize(
    ("absence_days", "expected"),
    [(1, "neutral"), (2, "neutral"), (3, "sad"), (14, "sleeping")],
)
def test_get_pet_endpoint_recomputes_mood(client, db_session, frozen_clock, absence_days, expected):
    token, user = register_user(client)
    last = (frozen_clock["now"] - timedelta(days=absence_days)).date()
    make_pet_with_last_activity(db_session, user["id"], last)
    db_session.commit()

    body = client.get("/api/v1/pet", headers=auth_header(token)).json()
    assert body["mood"] == expected
    assert body["last_activity_date"] == last.isoformat()
    assert body["days_since_last_activity"] == absence_days


def test_return_after_3_days_awards_bonus_and_event(
    client, db_session, frozen_clock, returned_events
):
    """Возвращение после 3 дней: +10 XP и событие `pet_returned` (D-14, PET-06).

    Часы перемоткой: первая тренировка «сегодня», вторая — через 3 дня.
    """
    _, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], NOW)
    assert pet.xp == 25

    # Перемотали управляемые часы на 3 дня вперёд — питомец «скучал».
    frozen_clock["now"] = NOW + timedelta(days=3)
    pet = pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])

    assert len(returned_events) == 1, "событие pet_returned опубликовано ровно один раз"
    assert returned_events[0]["user_id"] == user["id"]
    assert returned_events[0]["xp_bonus"] == pet_service.RETURN_BONUS_XP == 10
    assert returned_events[0]["days_absent"] == 3

    # 25 (первая тренировка) + 10 (бонус возвращения) + 25 (тренировка, серия сброшена).
    assert pet.xp == 60
    assert pet.streak_days == 1


def test_no_return_bonus_for_short_gap(client, db_session, frozen_clock, returned_events):
    """Разрыв 1–2 дня — бонуса нет; 3 дня — есть (проверка порога возвращения)."""
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], NOW)

    frozen_clock["now"] = NOW + timedelta(days=2)
    pet = pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    assert returned_events == [], "за 2 дня питомец не скучал — возвращения нет"
    before_xp = pet.xp

    frozen_clock["now"] = NOW + timedelta(days=5)
    pet = pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    assert len(returned_events) == 1, "разрыв 3 дня (день 2 -> день 5) засчитан как возвращение"
    assert pet.xp - before_xp == 25 + 10, "база 25 (серия сброшена) + 10 бонус"


def test_return_bonus_does_not_double_count_xp(client, db_session, frozen_clock, returned_events):
    """Бонус возвращения начисляется ровно один раз за тренировку (без двойного XP)."""
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], NOW)
    frozen_clock["now"] = NOW + timedelta(days=10)
    pet = pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    assert pet.xp == 25 + pet_service.RETURN_BONUS_XP + 25
    assert len(returned_events) == 1


def test_return_level_up_from_bonus_publishes_leveled_up(
    client, db_session, frozen_clock, returned_events
):
    """Если бонус возвращения пересёк порог уровня — уровень поднимается без двойного срабатывания."""
    _, user = register_user(client)
    pet = pet_service.get_or_create_pet(db_session, user["id"])
    pet.xp = 95  # до уровня 2 (порог 100 по D-13) не хватает 5
    pet.last_activity_date = (frozen_clock["now"] - timedelta(days=4)).date()
    db_session.flush()

    leveled: list[dict] = []
    handler = lambda payload, db: leveled.append(payload)  # noqa: E731
    pet_service.event_bus.subscribe("pet_leveled_up", handler)
    try:
        pet = pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    finally:
        pet_service.event_bus.unsubscribe("pet_leveled_up", handler)

    assert pet.level == 2, "бонус +10 перевёл питомца на уровень 2"
    assert pet.mood == "level_up"
    assert len(leveled) == 1, "pet_leveled_up опубликован ровно один раз"
    assert len(returned_events) == 1


def test_return_notification_is_created(client, db_session, frozen_clock):
    """Событие pet_returned → уведомление «Рад тебя видеть!» (через шину приложения)."""
    token, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], NOW)
    db_session.commit()
    frozen_clock["now"] = NOW + timedelta(days=4)
    pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    db_session.commit()

    notes = notification_service.list_notifications(db_session, user["id"])
    returned = [n for n in notes if n.kind == "pet_returned"]
    assert returned, "уведомление о возвращении создано"
    assert returned[0].title == "Рад тебя видеть!"


def test_return_bonus_via_api_full_path(client):
    """Сквозной путь POST /workouts/.../complete → pet_returned → уведомление (реальные часы)."""
    token, _ = register_user(client)
    headers = auth_header(token)

    done = complete_workout(client, headers)
    assert done["xp_awarded"] > 0

    me = client.get("/api/v1/auth/me", headers=headers).json()
    session = SessionLocal()
    try:
        pet = pet_service.get_pet(session, me["id"])
        pet.last_activity_date = pet.last_activity_date - timedelta(days=5)
        session.commit()
    finally:
        session.close()

    second = complete_workout(client, headers)
    assert second["xp_awarded"] > 0

    pet_body = client.get("/api/v1/pet", headers=headers).json()
    assert pet_body["mood"] == "happy", "свежая тренировка вернула хорошее настроение"

    notes = client.get("/api/v1/notifications", headers=headers).json()
    titles = [n["title"] for n in notes]
    assert "Рад тебя видеть!" in titles


def test_wakeup_after_sleeping_gets_return_bonus(client, db_session, frozen_clock, returned_events):
    """Пробуждение после сна (14+ дней) — сценарий из тикета: GET /pet → sleeping,
    затем тренировка даёт +10 XP и событие `pet_returned`."""
    token, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], NOW)
    db_session.commit()

    # Перемотали часы на 20 дней вперёд — пользователь открывает приложение.
    frozen_clock["now"] = NOW + timedelta(days=20)
    body = client.get("/api/v1/pet", headers=auth_header(token)).json()
    assert body["mood"] == "sleeping"

    pet_service.apply_workout_completed(db_session, user["id"], frozen_clock["now"])
    assert len(returned_events) == 1, "пробуждение засчитано как возвращение"
    assert returned_events[0]["days_absent"] == 20


def test_return_bonus_issued_once_per_training(client, db_session, frozen_clock, returned_events):
    """Повторный вызов обработчика для той же тренировки не выдаёт бонус дважды."""
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], NOW)
    db_session.commit()

    frozen_clock["now"] = NOW + timedelta(days=5)
    pet = pet_service.get_pet(db_session, user["id"])
    first = pet_service.handle_return_bonus(db_session, pet, frozen_clock["now"])
    pet_service.handle_return_bonus(db_session, pet, frozen_clock["now"])
    assert first == 10
    assert len(returned_events) == 1, "событие pet_returned опубликовано ровно один раз"
