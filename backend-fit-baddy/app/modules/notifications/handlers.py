from typing import Any

from app.events import (
    ACHIEVEMENT_EARNED,
    PET_LEVELED_UP,
    PET_RETURNED,
    QUEST_COMPLETED,
    WORKOUT_COMPLETED,
    WORKOUT_MISSED,
    EventBus,
)
from app.modules.notifications import service


def on_workout_completed(payload: dict[str, Any], db) -> None:
    service.create_notification(
        db,
        payload["user_id"],
        title="Workout completed",
        body="Great job! Your pet gained 25 XP.",
        kind="workout_completed",
    )


def on_workout_missed(payload: dict[str, Any], db) -> None:
    title = payload.get("title") or "scheduled workout"
    service.create_notification(
        db,
        payload["user_id"],
        title="Workout missed",
        body=f"Missed: {title}. Your pet is sad.",
        kind="workout_missed",
    )


def on_pet_leveled_up(payload: dict[str, Any], db) -> None:
    name = payload.get("name") or "Your pet"
    level = payload.get("level")
    service.create_notification(
        db,
        payload["user_id"],
        title="Pet leveled up",
        body=f"{name} reached level {level}!",
        kind="pet",
    )

def on_quest_completed(payload: dict[str, Any], db) -> None:
    title = payload.get("title") or "quest"
    reward = payload.get("xp_reward") or 0
    service.create_notification(
        db,
        payload["user_id"],
        title="Quest completed",
        body=f"{title}: +{reward} XP",
        kind="quest_completed",
    )


def on_achievement_earned(payload: dict[str, Any], db) -> None:
    title = payload.get("title") or "achievement"
    reward = payload.get("xp_reward") or 0
    service.create_notification(
        db,
        payload["user_id"],
        title="Achievement unlocked",
        body=f"{title}: +{reward} XP",
        kind="achievement_earned",
    )

def on_pet_returned(payload: dict[str, Any], db) -> None:
    bonus = payload.get("xp_bonus") or 0
    service.create_notification(
        db,
        payload["user_id"],
        title="Рад тебя видеть!",
        body=f"Добро пожаловать обратно: +{bonus} XP.",
        kind="pet_returned",
    )

def register(bus: EventBus) -> None:
    bus.subscribe(WORKOUT_COMPLETED, on_workout_completed)
    bus.subscribe(WORKOUT_MISSED, on_workout_missed)
    bus.subscribe(PET_LEVELED_UP, on_pet_leveled_up)
    bus.subscribe(PET_RETURNED, on_pet_returned)
    bus.subscribe(QUEST_COMPLETED, on_quest_completed)
    bus.subscribe(ACHIEVEMENT_EARNED, on_achievement_earned)