from typing import Any

from app.events import USER_REGISTERED, WORKOUT_COMPLETED, WORKOUT_MISSED, EventBus
from app.modules.pet import service


def on_user_registered(payload: dict[str, Any], db) -> None:
    service.get_or_create_pet(db, payload["user_id"])


def on_workout_completed(payload: dict[str, Any], db) -> None:
    service.apply_workout_completed(db, payload["user_id"], payload.get("completed_at"))


def on_workout_missed(payload: dict[str, Any], db) -> None:
    service.apply_workout_missed(db, payload["user_id"])


def register(bus: EventBus) -> None:
    bus.subscribe(USER_REGISTERED, on_user_registered)
    bus.subscribe(WORKOUT_COMPLETED, on_workout_completed)
    bus.subscribe(WORKOUT_MISSED, on_workout_missed)
