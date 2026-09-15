from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.events import PET_LEVELED_UP, event_bus
from app.modules.pet import models

XP_PER_WORKOUT = 25
XP_PER_LEVEL = 100
ENERGY_GAIN = 15
ENERGY_LOSS = 20
ENERGY_MIN = 0
ENERGY_MAX = 100


def get_pet(db: Session, user_id: int) -> models.Pet | None:
    return db.query(models.Pet).filter(models.Pet.user_id == user_id).first()


def get_or_create_pet(db: Session, user_id: int, name: str = "FitBuddy") -> models.Pet:
    pet = get_pet(db, user_id)
    if pet is None:
        pet = models.Pet(user_id=user_id, name=name)
        db.add(pet)
        db.flush()
    return pet


def apply_workout_completed(db: Session, user_id: int, completed_at) -> models.Pet:
    pet = get_or_create_pet(db, user_id)
    old_level = pet.level
    pet.xp += XP_PER_WORKOUT
    pet.level = pet.xp // XP_PER_LEVEL + 1
    pet.energy = min(ENERGY_MAX, pet.energy + ENERGY_GAIN)
    pet.updated_at = utc_now()

    when = completed_at.date() if hasattr(completed_at, "date") else utc_now().date()
    if pet.last_activity_date == when:
        pass
    elif pet.last_activity_date and pet.last_activity_date == when - timedelta(days=1):
        pet.streak_days += 1
    else:
        pet.streak_days = 1
    pet.last_activity_date = when

    if pet.level > old_level:
        pet.mood = "level_up"
        event_bus.publish(
            PET_LEVELED_UP,
            {"user_id": user_id, "level": pet.level, "name": pet.name},
            db,
        )
    else:
        pet.mood = "happy"
    db.flush()
    return pet


def apply_workout_missed(db: Session, user_id: int) -> models.Pet:
    pet = get_or_create_pet(db, user_id)
    pet.energy = max(ENERGY_MIN, pet.energy - ENERGY_LOSS)
    pet.mood = "sad"
    pet.streak_days = 0
    pet.updated_at = utc_now()
    db.flush()
    return pet


def pet_out(pet: models.Pet):
    from app.modules.pet.schemas import PetOut

    remaining = XP_PER_LEVEL - (pet.xp % XP_PER_LEVEL)
    if remaining == 0:
        remaining = XP_PER_LEVEL
    return PetOut(
        id=pet.id,
        name=pet.name,
        xp=pet.xp,
        xp_to_next_level=remaining,
        level=pet.level,
        energy=pet.energy,
        mood=pet.mood,
        streak_days=pet.streak_days,
        updated_at=pet.updated_at,
    )
