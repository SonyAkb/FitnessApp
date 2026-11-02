"""PET-09 — история событий питомца `pet_events` (xp, level_up, mood, return_bonus).

Ключевой критерий готовности: завершение тренировки пишет событие `xp`.
Дополнительно проверяются события уровня, настроения, бонуса возвращения
и статистика «сколько XP за неделю».
"""
from datetime import datetime, timedelta, timezone

from app.modules.pet import models
from app.modules.pet import service as pet_service
from tests.conftest import auth_header, complete_workout, register_user


def at(day: int) -> datetime:
    return datetime(2026, 10, day, 18, 0, tzinfo=timezone.utc)


def events_of_type(db, user_id: int, type_: str) -> list[models.PetEvent]:
    return (
        db.query(models.PetEvent)
        .filter(models.PetEvent.user_id == user_id, models.PetEvent.type == type_)
        .order_by(models.PetEvent.id)
        .all()
    )


def test_workout_completion_writes_xp_event(client, db_session):
    """Критерий готовности PET-09: завершение тренировки пишет событие xp."""
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    db_session.commit()

    xp_events = events_of_type(db_session, user["id"], pet_service.EVENT_XP)
    assert len(xp_events) == 1
    event = xp_events[0]
    assert event.amount == pet_service.XP_PER_WORKOUT  # +25 XP за тренировку
    assert event.xp_total == pet_service.XP_PER_WORKOUT
    assert event.level == 1
    assert event.mood == "happy"
    assert event.pet_id == pet_service.get_pet(db_session, user["id"]).id


def test_level_up_event_written_on_threshold(client, db_session):
    _, user = register_user(client)
    for day in range(1, 5):
        pet_service.apply_workout_completed(db_session, user["id"], at(day))
    db_session.commit()

    level_events = events_of_type(db_session, user["id"], pet_service.EVENT_LEVEL_UP)
    assert len(level_events) == 1
    assert level_events[0].amount == 2  # новый уровень = 2
    assert level_events[0].xp_total == 130  # 25+30+35+40 по D-13


def test_mood_change_and_return_bonus_events(client, db_session, monkeypatch):
    now = {"value": datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr(pet_service, "utc_now", lambda: now["value"])

    _, user = register_user(client)
    pet = pet_service.get_or_create_pet(db_session, user["id"])
    db_session.commit()

    pet.was_sleeping = True
    pet.last_activity_date = now["value"].date() - timedelta(days=5)
    db_session.commit()

    pet_service.apply_workout_completed(db_session, user["id"], now["value"])
    db_session.commit()

    bonus_events = events_of_type(db_session, user["id"], pet_service.EVENT_RETURN_BONUS)
    assert len(bonus_events) == 1
    assert bonus_events[0].amount == pet_service.RETURN_BONUS_XP

    pet = pet_service.get_pet(db_session, user["id"])
    pet.last_activity_date = now["value"].date() - timedelta(days=4)
    db_session.commit()
    pet_service.refresh_mood(db_session, pet)

    mood_events = events_of_type(db_session, user["id"], pet_service.EVENT_MOOD)
    assert len(mood_events) == 1
    assert mood_events[0].mood == "sad"


def test_weekly_xp_statistic(client, db_session):
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    pet_service.apply_workout_completed(db_session, user["id"], at(2))
    db_session.commit()

    now = datetime(2026, 10, 3, 0, 0, tzinfo=timezone.utc)
    assert pet_service.weekly_xp(db_session, user["id"], now=now) == 55


def test_workout_completed_via_api_writes_xp_event(client):
    """Путь через API: завершение тренировки публикует событие и пишет журнал."""
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)

    response = client.get("/api/v1/pet/events", headers=headers)
    assert response.status_code == 200
    types = [row["type"] for row in response.json()]
    assert "xp" in types

    stats = client.get("/api/v1/pet/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["weekly_xp"] >= pet_service.XP_PER_WORKOUT
