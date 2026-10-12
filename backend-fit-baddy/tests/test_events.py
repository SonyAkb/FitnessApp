"""In-process event bus and module wiring (architecture rule: modules react to events, not to each other)."""
from app.events import (
    PET_LEVELED_UP,
    USER_REGISTERED,
    WORKOUT_COMPLETED,
    WORKOUT_MISSED,
    EventBus,
    event_bus,
)


def test_publish_calls_all_subscribers_in_order():
    bus = EventBus()
    calls = []
    bus.subscribe("e", lambda payload, db: calls.append(("a", payload["x"])))
    bus.subscribe("e", lambda payload, db: calls.append(("b", payload["x"])))
    bus.publish("e", {"x": 1})
    assert calls == [("a", 1), ("b", 1)]


def test_publish_without_subscribers_is_noop():
    EventBus().publish("nobody-listens", {})


def test_application_wires_expected_consumers(client):
    handlers = event_bus._handlers
    modules = lambda name: {h.__module__ for h in handlers[name]}  # noqa: E731
    assert modules(USER_REGISTERED) == {"app.modules.pet.handlers", "app.modules.subscription.handlers"}
    assert modules(WORKOUT_COMPLETED) == {"app.modules.pet.handlers", "app.modules.notifications.handlers"}
    assert modules(WORKOUT_MISSED) == {"app.modules.pet.handlers", "app.modules.notifications.handlers"}
    assert modules(PET_LEVELED_UP) == {"app.modules.notifications.handlers"}
