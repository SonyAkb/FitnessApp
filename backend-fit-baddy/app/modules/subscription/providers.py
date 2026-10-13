"""Payment providers. Business logic talks to PaymentProvider, never to a concrete provider."""
import uuid
from dataclasses import dataclass
from typing import Protocol

PRO_PRICE_CENTS = 999


@dataclass(frozen=True)
class CheckoutSession:
    checkout_id: str
    amount: int
    currency: str
    status: str  # pending | succeeded | failed


class PaymentProvider(Protocol):
    name: str

    def create_checkout(self, user_id: int, plan: str) -> CheckoutSession: ...


class SandboxPaymentProvider:
    """Mock provider for the educational MVP: no external calls, the payment always succeeds."""

    name = "sandbox"

    def create_checkout(self, user_id: int, plan: str) -> CheckoutSession:
        return CheckoutSession(
            checkout_id=f"mock_chk_{uuid.uuid4().hex[:12]}",
            amount=PRO_PRICE_CENTS,
            currency="usd",
            status="succeeded",
        )


def get_payment_provider() -> PaymentProvider:
    return SandboxPaymentProvider()
