"""PET-08 — прогресс квестов, награды XP, выдача достижений, сброс daily/weekly (US-D3).

Тесты на каждый квест и каждое достижение + уведомление о завершении квеста.
"""
from datetime import datetime, timedelta, timezone

from app.modules.pet import service as pet_service
from tests.conftest import auth_header, complete_workout, register_user


def at(day: int, hour: int = 18) -> datetime:
    return datetime(2026, 10, day, hour, 0, tzinfo=timezone.utc)


def quest_map(client, headers):
    body = client.get("/api/v1/pet/quests", headers=headers).json()
    return {q["code"]: q for q in body}


def achievement_codes(client, headers):
    return {a["code"] for a in client.get("/api/v1/pet/achievements", headers=headers).json()}


def test_catalog_is_seeded_lazily(client, db_session):
    _, user = register_user(client)
    pet_service.ensure_catalog(db_session)
    codes = {q.code for q in db_session.query(pet_service.models.Quest).all()}
    assert codes == {"one_workout_today", "three_workouts_week"}
    assert {"first_workout", "three_in_row", "week_no_miss"} <= {
        a.code for a in db_session.query(pet_service.models.Achievement).all()
    }


def test_daily_quest_completes_on_first_workout_and_awards_xp(client, db_session):
    token, user = register_user(client)
    before = pet_service.get_pet(db_session, user["id"]).xp
    finished = pet_service.apply_quest_progress(db_session, user["id"], at(1))
    db_session.commit()

    assert [q.code for q in finished] == ["one_workout_today"]
    pet = pet_service.get_pet(db_session, user["id"])
    assert pet.xp == before + 20, "награда daily-квеста = xp_reward из справочника"
    q = quest_map(client, auth_header(token))["one_workout_today"]
    assert (q["progress"], q["target"], q["status"]) == (1, 1, "completed")
    assert q["deadline"] is not None and q["completed_at"] is not None


def test_second_workout_same_day_does_not_recomplete_daily_quest(client, db_session):
    _, user = register_user(client)
    pet_service.apply_quest_progress(db_session, user["id"], at(1))
    before = pet_service.get_pet(db_session, user["id"]).xp
    finished = pet_service.apply_quest_progress(db_session, user["id"], at(1))
    db_session.commit()
    assert finished == []
    assert pet_service.get_pet(db_session, user["id"]).xp == before


def test_weekly_quest_needs_three_workouts(client, db_session):
    _, user = register_user(client)
    for day in (1, 2):
        pet_service.apply_quest_progress(db_session, user["id"], at(day))
    db_session.commit()
    rows = dict((q.code, uq.progress) for uq, q in pet_service.list_user_quests(db_session, user["id"]))
    assert rows["three_workouts_week"] == 2
    assert rows["one_workout_today"] == 1, "daily сброшен на новый день"

    finished = pet_service.apply_quest_progress(db_session, user["id"], at(3))
    db_session.commit()
    assert [q.code for q in finished] == ["three_workouts_week"]
    assert pet_service.get_pet(db_session, user["id"]).xp == 3 * 20 + 50, "три daily + одна weekly награда"


def test_daily_reset_when_period_changes(client, db_session):
    _, user = register_user(client)
    pet_service.apply_quest_progress(db_session, user["id"], at(1))
    db_session.commit()
    pet_service.apply_quest_progress(db_session, user["id"], at(2))
    db_session.commit()
    rows = {q.code: (uq.progress, uq.completed_at) for uq, q in pet_service.list_user_quests(db_session, user["id"])}
    assert rows["one_workout_today"][0] == 1, "новый день — прогресс снова 1, а не 2"
    assert rows["one_workout_today"][1] is not None


def test_weekly_reset_on_new_iso_week(client, db_session):
    _, user = register_user(client)
    for day in (5, 6, 7):  # Mon-Wed 2026-10-05..07 belong to the same ISO week
        pet_service.apply_quest_progress(db_session, user["id"], at(day))
    db_session.commit()
    next_week = pet_service.apply_quest_progress(db_session, user["id"], at(12))
    db_session.commit()
    assert next_week == [], "неделя началась — недельный квест снова в процессе"
    rows = {q.code: uq.progress for uq, q in pet_service.list_user_quests(db_session, user["id"])}
    assert rows["three_workouts_week"] == 1


def test_period_start_boundaries():
    moment = datetime(2026, 10, 8, 15, 30, tzinfo=timezone.utc)  # Thursday
    assert pet_service.period_start(moment, "daily") == datetime(2026, 10, 8, tzinfo=timezone.utc)
    assert pet_service.period_start(moment, "weekly") == datetime(2026, 10, 5, tzinfo=timezone.utc)
    assert pet_service.deadline_for(datetime(2026, 10, 5, tzinfo=timezone.utc), "weekly") == \
        datetime(2026, 10, 12, tzinfo=timezone.utc)


def test_first_workout_achievement_issued_once(client, db_session):
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    earned = pet_service.evaluate_achievements(db_session, user["id"], at(1))
    db_session.commit()
    assert [a.code for a in earned] == ["first_workout"]
    again = pet_service.evaluate_achievements(db_session, user["id"], at(1))
    assert again == [], "достижение не выдаётся повторно (uq_user_achievement)"


def test_three_in_row_achievement_after_streak_of_three(client, db_session):
    _, user = register_user(client)
    for day in (1, 2):
        pet_service.apply_workout_completed(db_session, user["id"], at(day))
        assert "three_in_row" not in [a.code for a in pet_service.evaluate_achievements(db_session, user["id"], at(day))]
    pet_service.apply_workout_completed(db_session, user["id"], at(3))
    earned = pet_service.evaluate_achievements(db_session, user["id"], at(3))
    db_session.commit()
    assert "three_in_row" in [a.code for a in earned]
    assert pet_service.get_pet(db_session, user["id"]).streak_days == 3


def test_week_no_miss_achievement_after_seven_day_streak(client, db_session):
    _, user = register_user(client)
    for day in range(1, 8):
        pet_service.apply_workout_completed(db_session, user["id"], at(day))
    earned = pet_service.evaluate_achievements(db_session, user["id"], at(7))
    db_session.commit()
    codes = [a.code for a in earned]
    assert "week_no_miss" in codes
    assert pet_service.get_pet(db_session, user["id"]).streak_days == 7


def test_achievement_xp_is_awarded(client, db_session):
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    before = pet_service.get_pet(db_session, user["id"]).xp
    pet_service.evaluate_achievements(db_session, user["id"], at(1))
    db_session.commit()
    assert pet_service.get_pet(db_session, user["id"]).xp == before + 10


def test_quests_endpoint_shape_and_auth(client):
    token, _ = register_user(client)
    body = client.get("/api/v1/pet/quests", headers=auth_header(token)).json()
    assert len(body) == 2
    first = body[0]
    assert set(first) == {"id", "code", "title", "description", "period", "progress",
                          "target", "xp_reward", "status", "deadline", "completed_at"}
    assert client.get("/api/v1/pet/quests").status_code == 401
    assert client.get("/api/v1/pet/achievements").status_code == 401


def test_achievements_endpoint_returns_earned_with_date(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    assert client.get("/api/v1/pet/achievements", headers=headers).json() == []
    complete_workout(client, headers)
    items = client.get("/api/v1/pet/achievements", headers=headers).json()
    assert [i["code"] for i in items] == ["first_workout"]
    assert items[0]["earned_at"] is not None and items[0]["xp_reward"] == 10


def test_quest_completion_creates_notification(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)
    notes = client.get("/api/v1/notifications", headers=headers).json()
    kinds = [n["kind"] for n in notes]
    assert "quest_completed" in kinds, "DoD PET-08: уведомление о завершении квеста"
    assert "achievement_earned" in kinds


def test_full_event_path_updates_quest_progress(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)
    q = quest_map(client, headers)["one_workout_today"]
    assert q["status"] == "completed" and q["progress"] == 1
    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["xp"] == 25 + 20 + 10, "тренировка + награда квеста + достижение"