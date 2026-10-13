"""Module 5 — AI recommendations and subscription (US-G1, US-G2, US-H2; AC10.x, AC11.x)."""
from app.modules.subscription import service as subscription_service
from app.modules.subscription.providers import CheckoutSession
from tests.conftest import WEBHOOK_HEADERS, auth_header, complete_workout, register_user


def webhook(client, event_id, user_id, event_type="payment.succeeded", headers=WEBHOOK_HEADERS):
    return client.post(
        "/api/v1/subscription/webhook",
        json={"event_id": event_id, "type": event_type, "user_id": user_id},
        headers=headers,
    )


def test_new_user_is_on_free_plan(client):
    token, _ = register_user(client)
    sub = client.get("/api/v1/subscription", headers=auth_header(token)).json()
    assert sub["plan"] == "free"
    assert "ai_recommendations" not in sub["entitlements"]


def test_ai_requires_pro(client):
    token, _ = register_user(client)
    response = client.get("/api/v1/ai/recommend", headers=auth_header(token))
    assert response.status_code == 403
    assert "Pro" in response.json()["detail"]


def test_checkout_activates_pro_and_unlocks_ai(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    checkout = client.post("/api/v1/subscription/checkout", json={"plan": "pro"}, headers=headers)
    assert checkout.status_code == 200
    assert checkout.json()["mock"] is True
    assert checkout.json()["checkout_id"].startswith("mock_chk_")
    assert client.get("/api/v1/subscription", headers=headers).json()["plan"] == "pro"

    complete_workout(client, headers)
    rec = client.get("/api/v1/ai/recommend", headers=headers)
    assert rec.status_code == 200
    body = rec.json()
    assert body["recommendation"] and body["reason"] and body["disclaimer"]
    history = client.get("/api/v1/ai/history", headers=headers).json()
    assert [item["id"] for item in history] == [body["id"]]


def test_ai_history_is_empty_initially(client):
    token, _ = register_user(client)
    assert client.get("/api/v1/ai/history", headers=auth_header(token)).json() == []


def test_webhook_without_or_with_wrong_signature_is_forbidden(client):
    _, user = register_user(client)
    assert webhook(client, "evt_1", user["id"], headers={}).status_code == 403
    assert webhook(client, "evt_1", user["id"], headers={"X-Mock-Signature": "wrong"}).status_code == 403
    token, _ = register_user(client, email="other@example.com")
    assert client.get("/api/v1/subscription", headers=auth_header(token)).json()["plan"] == "free"


def test_webhook_is_idempotent(client):
    token, user = register_user(client)
    first = webhook(client, "evt_1", user["id"])
    second = webhook(client, "evt_1", user["id"])
    assert first.json()["duplicate"] is False and first.json()["plan"] == "pro"
    assert second.json()["duplicate"] is True and second.json()["plan"] == "pro"


def test_failed_payment_keeps_free_plan(client, db_session):
    token, user = register_user(client)
    response = webhook(client, "evt_fail", user["id"], event_type="payment.failed")
    assert response.status_code == 200
    assert response.json()["plan"] == "free"
    from app.modules.subscription import models

    statuses = [p.status for p in db_session.query(models.Payment).filter_by(user_id=user["id"])]
    assert statuses == ["failed"]


def test_pending_provider_does_not_activate_pro(client, db_session):
    _, user = register_user(client)

    class PendingProvider:
        name = "pending-test"

        def create_checkout(self, user_id, plan):
            return CheckoutSession(checkout_id="chk_pending", amount=999, currency="usd", status="pending")

    result = subscription_service.checkout(db_session, user["id"], provider=PendingProvider())
    assert result.status == "pending"
    assert subscription_service.can_use(db_session, user["id"], "ai_recommendations") is False


def test_can_use_by_plan(client, db_session):
    _, user = register_user(client)
    assert subscription_service.can_use(db_session, user["id"], "workouts") is True
    assert subscription_service.can_use(db_session, user["id"], "ai_recommendations") is False
    subscription_service.activate_pro(db_session, user["id"])
    assert subscription_service.can_use(db_session, user["id"], "ai_recommendations") is True
