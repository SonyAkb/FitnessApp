from typing import Any

from app.events import PET_LEVELED_UP, WORKOUT_COMPLETED, WORKOUT_MISSED, EventBus
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


def register(bus: EventBus) -> None:
    bus.subscribe(WORKOUT_COMPLETED, on_workout_completed)
    bus.subscribe(WORKOUT_MISSED, on_workout_missed)
    bus.subscribe(PET_LEVELED_UP, on_pet_leveled_up)
