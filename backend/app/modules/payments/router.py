"""
MVP: создание Checkout-сессии и приём вебхука Stripe (тестовый режим).
TODO(module-4):
  - обработать остальные типы событий вебхука (invoice.payment_failed, customer.subscription.deleted)
  - endpoint отмены подписки
  - привязка фичей к плану (например, ai/recommend доступен только "pro")
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.users_schedule.models import User
from . import schemas, service, stripe_client

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/subscription", response_model=schemas.SubscriptionRead)
def get_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.get_or_create_subscription(db, current_user.id)


@router.post("/create-checkout-session", response_model=schemas.CheckoutSessionRead)
def create_checkout_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not stripe_client.settings.STRIPE_SECRET_KEY if hasattr(stripe_client, "settings") else False:
        pass  # оставлено намеренно пустым: проверка ниже
    try:
        url = stripe_client.create_checkout_session(current_user.email, current_user.id)
    except Exception as exc:  # noqa: BLE001 — в MVP ловим широко, чтобы вернуть понятную ошибку
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось создать Stripe checkout сессию. Проверьте STRIPE_* переменные в .env. ({exc})",
        )
    return schemas.CheckoutSessionRead(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe_client.construct_webhook_event(payload, sig_header)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {exc}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["client_reference_id"])
        service.activate_subscription(
            db,
            user_id=user_id,
            stripe_customer_id=session.get("customer", ""),
            stripe_subscription_id=session.get("subscription", ""),
        )
    # TODO(module-4): остальные event["type"] по необходимости

    return {"received": True}
