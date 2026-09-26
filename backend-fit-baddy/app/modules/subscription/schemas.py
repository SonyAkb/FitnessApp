from pydantic import BaseModel


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    entitlements: list[str] = []
    current_period_end: str | None = None


class CheckoutIn(BaseModel):
    plan: str = "pro"


class CheckoutOut(BaseModel):
    plan: str
    status: str
    checkout_id: str
    message: str
    mock: bool = True


class WebhookIn(BaseModel):
    event_id: str
    type: str
    user_id: int | None = None
    plan: str | None = "pro"


class WebhookOut(BaseModel):
    received: bool = True
    duplicate: bool = False
    plan: str | None = None
    status: str
    event_id: str
