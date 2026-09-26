import uuid

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.modules.subscription import models, schemas

PRO_ENTITLEMENTS = ["ai_recommendations"]


def get_or_create_subscription(db: Session, user_id: int) -> models.Subscription:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if sub is None:
        sub = models.Subscription(user_id=user_id, plan="free", status="active")
        db.add(sub)
        db.flush()
    return sub


def to_out(sub: models.Subscription) -> schemas.SubscriptionOut:
    entitlements = ["workouts", "pet", "dashboard"]
    if sub.plan == "pro":
        entitlements = entitlements + list(PRO_ENTITLEMENTS)
    return schemas.SubscriptionOut(
        plan=sub.plan,
        status=sub.status,
        entitlements=entitlements,
        current_period_end=None,
    )


def activate_pro(db: Session, user_id: int) -> models.Subscription:
    sub = get_or_create_subscription(db, user_id)
    sub.plan = "pro"
    sub.status = "active"
    sub.updated_at = utc_now()
    db.add(
        models.Payment(
            user_id=user_id,
            amount=999,
            currency="usd",
            status="succeeded",
            provider="sandbox",
        )
    )
    db.flush()
    return sub


def checkout(db: Session, user_id: int) -> schemas.CheckoutOut:
    activate_pro(db, user_id)
    checkout_id = f"mock_chk_{uuid.uuid4().hex[:12]}"
    return schemas.CheckoutOut(
        plan="pro",
        status="active",
        checkout_id=checkout_id,
        message="Sandbox checkout completed. Pro plan activated.",
        mock=True,
    )


def process_webhook(db: Session, data: schemas.WebhookIn) -> schemas.WebhookOut:
    existing = db.query(models.WebhookEvent).filter(models.WebhookEvent.event_id == data.event_id).first()
    if existing:
        sub = get_or_create_subscription(db, data.user_id) if data.user_id else None
        return schemas.WebhookOut(
            received=True,
            duplicate=True,
            event_id=data.event_id,
            plan=sub.plan if sub else data.plan,
            status="duplicate",
        )

    event = models.WebhookEvent(
        event_id=data.event_id,
        event_type=data.type,
        user_id=data.user_id,
    )
    db.add(event)
    db.flush()

    plan = "free"
    sub_status = "active"
    if data.user_id is not None and data.type in {
        "checkout.completed",
        "subscription.activated",
        "payment.succeeded",
    }:
        sub = activate_pro(db, data.user_id)
        plan = sub.plan
        sub_status = sub.status
    elif data.user_id is not None:
        sub = get_or_create_subscription(db, data.user_id)
        plan = sub.plan
        sub_status = sub.status

    return schemas.WebhookOut(
        received=True,
        duplicate=False,
        event_id=data.event_id,
        plan=plan,
        status=sub_status if sub_status != "duplicate" else "processed",
    )
