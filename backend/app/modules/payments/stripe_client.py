"""
Тонкая обёртка над stripe-sdk, чтобы держать все stripe.* вызовы в одном месте.
Используется ТОЛЬКО тестовый (sandbox) режим — ключи из .env начинаются с sk_test_/pk_test_.
"""
import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user_email: str, user_id: int) -> str:
    """
    Создаёт тестовую Stripe Checkout сессию на подписку "pro".
    Требует STRIPE_PRICE_ID_PRO — id тестовой цены, созданной в Stripe Dashboard (test mode).
    Возвращает URL, на который нужно перенаправить пользователя.
    """
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=user_email,
        line_items=[{"price": settings.STRIPE_PRICE_ID_PRO, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=str(user_id),
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
