from typing import Any

from app.events import USER_REGISTERED, EventBus
from app.modules.subscription import service


def on_user_registered(payload: dict[str, Any], db) -> None:
    service.get_or_create_subscription(db, payload["user_id"])


def register(bus: EventBus) -> None:
    bus.subscribe(USER_REGISTERED, on_user_registered)
