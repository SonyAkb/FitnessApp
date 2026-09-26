"""In-process event bus. Modules subscribe to names; they never import each other's models."""
from collections import defaultdict
from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any], Any], None]

USER_REGISTERED = "user_registered"
WORKOUT_COMPLETED = "workout_completed"
WORKOUT_MISSED = "workout_missed"
PET_LEVELED_UP = "pet_leveled_up"


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    def publish(self, event_name: str, payload: dict[str, Any], db: Any = None) -> None:
        for handler in list(self._handlers.get(event_name, [])):
            handler(payload, db)


event_bus = EventBus()
_handlers_registered = False


def register_event_handlers() -> None:
    global _handlers_registered
    if _handlers_registered:
        return

    from app.modules.notifications.handlers import register as register_notifications
    from app.modules.pet.handlers import register as register_pet
    from app.modules.subscription.handlers import register as register_subscription

    register_pet(event_bus)
    register_notifications(event_bus)
    register_subscription(event_bus)
    _handlers_registered = True
