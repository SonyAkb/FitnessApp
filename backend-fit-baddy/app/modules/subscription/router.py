from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.subscription import schemas, service

router = APIRouter(tags=["subscription"])


@router.get("/subscription", response_model=schemas.SubscriptionOut)
def get_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = service.get_or_create_subscription(db, current_user.id)
    db.commit()
    return service.to_out(sub)


@router.post("/subscription/checkout", response_model=schemas.CheckoutOut)
def checkout(
    data: schemas.CheckoutIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ = data
    result = service.checkout(db, current_user.id)
    db.commit()
    return result


@router.post("/subscription/webhook", response_model=schemas.WebhookOut)
def webhook(data: schemas.WebhookIn, db: Session = Depends(get_db)):
    result = service.process_webhook(db, data)
    db.commit()
    return result
