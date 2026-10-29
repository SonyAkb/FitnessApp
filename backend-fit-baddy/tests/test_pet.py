"""Module 3 — pet rules: XP, level, mood, energy, streak (US-D1, US-D2; AC1.4, AC5.x, AC6.x).

Unit tests call `pet.service` directly; API tests check the event-driven path.
"""
from datetime import datetime, timedelta, timezone

from app.modules.pet import service as pet_service
from tests.conftest import auth_header, complete_workout, register_user


def at(day: int) -> datetime:
    return datetime(2026, 10, day, 18, 0, tzinfo=timezone.utc)


def test_new_pet_defaults(client, db_session):
    _, user = register_user(client)
    pet = pet_service.get_pet(db_session, user["id"])
    assert (pet.xp, pet.level, pet.mood, pet.streak_days) == (0, 1, "idle", 0)
    assert 0 <= pet.energy <= 100


def test_workout_gives_xp_happy_mood_and_streak(client, db_session):
    _, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(1))
    assert pet.xp == pet_service.XP_PER_WORKOUT
    assert pet.mood == "happy"
    assert pet.streak_days == 1


def test_level_up_when_threshold_reached(client, db_session):
    _, user = register_user(client)
    for day in range(1, 5):
        pet = pet_service.apply_workout_completed(db_session, user["id"], at(day))
    # D-13: 25 + 30 + 35 + 40 = 130 XP; порог 1->2 равен 1*100 (накопительный).
    assert pet.xp == 130
    assert pet.level == 2
    assert pet.mood == "level_up"


def test_streak_bonus_adds_5_xp_per_extra_day(client, db_session):
    _, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(1))
    assert pet.xp == pet_service.XP_PER_WORKOUT == 25
    assert pet.streak_days == 1

    # Второй день серии: бонус +5*(2-1) => 30 XP.
    before = pet.xp
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(2))
    assert pet.xp - before == 30
    assert pet.streak_days == 2

    # Повторная тренировка в тот же день серию не увеличивает.
    before = pet.xp
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(2))
    assert pet.xp - before == 30

    # Разрыв в днях обнуляет серию -> снова базовые 25 XP.
    before = pet.xp
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(9))
    assert pet.xp - before == pet_service.XP_PER_WORKOUT + pet_service.RETURN_BONUS_XP
    assert pet.streak_days == 1


def test_xp_for_workout_is_public_and_pure(client, db_session):
    """`xp_for_workout(pet, completed_at)` — публичная функция без мутации (WKT-09)."""
    _, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(1))
    xp_before, streak_before = pet.xp, pet.streak_days

    assert pet_service.xp_for_workout(pet, at(1)) == 25, "тот же день — серия растёт на 1"
    assert pet_service.xp_for_workout(pet, at(2)) == 30, "следующий день серии"
    assert pet_service.xp_for_workout(pet, at(7)) == 25, "разрыв серии"
    assert (pet.xp, pet.streak_days) == (xp_before, streak_before), "без побочных эффектов"


def test_cumulative_level_threshold_is_level_times_100(client, db_session):
    """Порог уровня n -> n+1 = n*100, накопительно (D-13)."""
    assert pet_service.xp_threshold_for_level(1) == 100
    assert pet_service.xp_threshold_for_level(2) == 200
    assert pet_service.total_xp_for_level(3) == 300, "100 + 200"

    assert pet_service.level_for_xp(99) == 1
    assert pet_service.level_for_xp(100) == 2
    assert pet_service.level_for_xp(299) == 2
    assert pet_service.level_for_xp(300) == 3
    assert pet_service.xp_to_next_level(1, 55) == 100
    # Порог уровня n -> n+1 = n*100 — полный шаг; излишек прошлого уровня не вычитается.
    assert pet_service.xp_to_next_level(2, 130) == 200
    assert pet_service.xp_to_next_level(2, 100) == 200


def test_level_capped_at_max(client, db_session):
    """Максимум MAX_LEVEL = 50 уровней; дальше XP копится, уровень не растёт."""
    _, user = register_user(client)
    pet = pet_service.get_or_create_pet(db_session, user["id"])
    pet.xp = pet_service.total_xp_for_level(pet_service.MAX_LEVEL)
    pet.level = pet_service.level_for_xp(pet.xp)
    assert pet.level == pet_service.MAX_LEVEL == 50

    out = pet_service.pet_out(pet)
    assert out.xp_to_next_level == 0, "на потолке до следующего уровня ничего не нужно"

    before_level = pet.level
    pet_service.award_xp(db_session, pet, 500)
    assert pet.level == before_level, "потолок не пробивается наградами квестов"
    assert pet.xp > out.xp, "XP продолжает накапливаться"


def test_streak_counts_consecutive_days_only(client, db_session):
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    pet_service.apply_workout_completed(db_session, user["id"], at(2))
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(2))
    assert pet.streak_days == 2, "second workout on the same day keeps the streak"
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(5))
    assert pet.streak_days == 1, "a gap resets the streak"


def test_missed_workout_makes_pet_sad_and_tired(client, db_session):
    _, user = register_user(client)
    pet_service.apply_workout_completed(db_session, user["id"], at(1))
    before = pet_service.get_pet(db_session, user["id"]).energy
    pet = pet_service.apply_workout_missed(db_session, user["id"])
    assert pet.mood == "sad"
    assert pet.energy < before
    assert pet.streak_days == 0


def test_energy_stays_within_bounds(client, db_session):
    _, user = register_user(client)
    for _ in range(10):
        pet = pet_service.apply_workout_missed(db_session, user["id"])
    assert pet.energy == 0
    for day in range(1, 12):
        pet = pet_service.apply_workout_completed(db_session, user["id"], at(day))
    assert pet.energy == 100
    assert pet.level >= 1 and pet.xp >= 0


def test_xp_to_next_level(client, db_session):
    _, user = register_user(client)
    pet = pet_service.apply_workout_completed(db_session, user["id"], at(1))
    out = pet_service.pet_out(pet)
    # Порог 1->2 = level*100 = 100 (решение D-13).
    assert pet.xp == pet_service.XP_PER_WORKOUT
    assert out.xp_to_next_level == 100


def test_pet_reacts_to_completed_workout_via_api(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    done = complete_workout(client, headers)
    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["xp"] == done["xp_awarded"] + 20 + 10, "квест + достижение"
    assert pet["mood"] == "happy"


def test_xp_is_consistent_between_pet_and_dashboard(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    total = sum(complete_workout(client, headers)["xp_awarded"] for _ in range(2))
    pet = client.get("/api/v1/pet", headers=headers).json()
    summary = client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert pet["xp"] == summary["xp"] == total + 20 + 10, "награда daily-квеста + первое достижение"
    assert pet["streak_days"] == summary["current_streak_days"]


def test_missed_slot_affects_pet_via_event(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    slot = client.post(
        "/api/v1/schedule",
        json={"title": "A", "starts_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()},
        headers=headers,
    ).json()
    client.post(f"/api/v1/schedule/{slot['id']}/miss", headers=headers)
    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["mood"] == "sad"
    assert pet["energy"] < 50
