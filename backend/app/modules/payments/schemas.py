from datetime import datetime
from pydantic import BaseModel


class SubscriptionRead(BaseModel):
    plan: str
    status: str
    current_period_end: datetime | None

    class Config:
        from_attributes = True


class CheckoutSessionRead(BaseModel):
    checkout_url: str


class PaymentRead(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
