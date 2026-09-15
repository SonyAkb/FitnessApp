from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.clock import utc_now
from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan = Column(String, nullable=False, default="free")  # free | pro
    status = Column(String, nullable=False, default="active")
    updated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False, default=0)
    currency = Column(String, nullable=False, default="usd")
    status = Column(String, nullable=False, default="succeeded")
    provider = Column(String, nullable=False, default="sandbox")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_webhook_event_id"),)

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, nullable=False, unique=True, index=True)
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, nullable=True)
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
