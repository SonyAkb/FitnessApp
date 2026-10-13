import hmac

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import settings
from app.modules.subscription import models, schemas
from app.modules.subscription.providers import PRO_PRICE_CENTS, PaymentProvider, get_payment_provider

FREE_ENTITLEMENTS = ["workouts", "pet", "dashboard"]
PRO_ENTITLEMENTS = ["ai_recommendations"]

SUCCESS_EVENTS = {"payment.succeeded", "checkout.completed", "subscription.activated"}
FAILURE_EVENTS = {"payment.failed"}


def get_or_create_subscription(db: Session, user_id: int) -> models.Subscription:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if sub is None:
        sub = models.Subscription(user_id=user_id, plan="free", status="active")
        db.add(sub)
        db.flush()
    return sub


def entitlements_for(plan: str) -> list[str]:
    if plan == "pro":
        return FREE_ENTITLEMENTS + PRO_ENTITLEMENTS
    return list(FREE_ENTITLEMENTS)


def can_use(db: Session, user_id: int, feature: str) -> bool:
    """Single entitlement check used by other modules instead of `plan == "pro"` checks."""
    sub = get_or_create_subscription(db, user_id)
    return sub.status == "active" and feature in entitlements_for(sub.plan)


def to_out(sub: models.Subscription) -> schemas.SubscriptionOut:
    return schemas.SubscriptionOut(
        plan=sub.plan,
        status=sub.status,
        entitlements=entitlements_for(sub.plan),
        current_period_end=None,
    )


def activate_pro(db: Session, user_id: int) -> models.Subscription:
    sub = get_or_create_subscription(db, user_id)
    sub.plan = "pro"
    sub.status = "active"
    sub.updated_at = utc_now()
    db.flush()
    return sub


def record_payment(
    db: Session, user_id: int, status: str, provider: str, amount: int = 0, currency: str = "usd"
) -> models.Payment:
    payment = models.Payment(
        user_id=user_id, amount=amount, currency=currency, status=status, provider=provider
    )
    db.add(payment)
    db.flush()
    return payment


def checkout(db: Session, user_id: int, provider: PaymentProvider | None = None) -> schemas.CheckoutOut:
    provider = provider or get_payment_provider()
    session = provider.create_checkout(user_id, "pro")
    record_payment(db, user_id, session.status, provider.name, session.amount, session.currency)
    if session.status == "succeeded":
        sub = activate_pro(db, user_id)
        message = "Sandbox checkout completed. Pro plan activated."
    else:
        sub = get_or_create_subscription(db, user_id)
        message = "Waiting for payment confirmation."
    return schemas.CheckoutOut(
        plan=sub.plan,
        status=session.status if session.status != "succeeded" else sub.status,
        checkout_id=session.checkout_id,
        message=message,
        mock=True,
    )


def signature_is_valid(signature: str | None) -> bool:
    if not signature:
        return False
    return hmac.compare_digest(signature, settings.MOCK_WEBHOOK_SECRET)


def process_webhook(db: Session, data: schemas.WebhookIn) -> schemas.WebhookOut:
    existing = db.query(models.WebhookEvent).filter(models.WebhookEvent.event_id == data.event_id).first()
    if existing:
        sub = get_or_create_subscription(db, data.user_id) if data.user_id else None
        return schemas.WebhookOut(
            received=True,
            duplicate=True,
            event_id=data.event_id,
            plan=sub.plan if sub else None,
            status="duplicate",
        )
    db.add(models.WebhookEvent(event_id=data.event_id, event_type=data.type, user_id=data.user_id))
    db.flush()

    if data.user_id is None:
        return schemas.WebhookOut(received=True, duplicate=False, event_id=data.event_id, status="ignored")

    if data.type in SUCCESS_EVENTS:
        record_payment(db, data.user_id, "succeeded", "sandbox", PRO_PRICE_CENTS)
        sub = activate_pro(db, data.user_id)
    else:
        if data.type in FAILURE_EVENTS:
            record_payment(db, data.user_id, "failed", "sandbox", PRO_PRICE_CENTS)
        sub = get_or_create_subscription(db, data.user_id)
    return schemas.WebhookOut(
        received=True,
        duplicate=False,
        event_id=data.event_id,
        plan=sub.plan,
        status=sub.status,
    )
