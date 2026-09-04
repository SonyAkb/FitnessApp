from datetime import datetime

from sqlalchemy.orm import Session
from . import models


def get_or_create_subscription(db: Session, user_id: int) -> models.Subscription:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if not sub:
        sub = models.Subscription(user_id=user_id)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


def activate_subscription(db: Session, user_id: int, stripe_customer_id: str, stripe_subscription_id: str):
    sub = get_or_create_subscription(db, user_id)
    sub.plan = "pro"
    sub.status = "active"
    sub.stripe_customer_id = stripe_customer_id
    sub.stripe_subscription_id = stripe_subscription_id
    sub.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sub)
    return sub
