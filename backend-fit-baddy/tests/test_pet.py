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
    assert pet.xp == 4 * pet_service.XP_PER_WORKOUT
    assert pet.level == 2
    assert pet.mood == "level_up"


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
    assert out.xp_to_next_level == pet_service.XP_PER_LEVEL - pet_service.XP_PER_WORKOUT


def test_pet_reacts_to_completed_workout_via_api(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    done = complete_workout(client, headers)
    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["xp"] == done["xp_awarded"]
    assert pet["mood"] == "happy"


def test_xp_is_consistent_between_pet_and_dashboard(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    total = sum(complete_workout(client, headers)["xp_awarded"] for _ in range(2))
    pet = client.get("/api/v1/pet", headers=headers).json()
    summary = client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert pet["xp"] == summary["xp"] == total
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
