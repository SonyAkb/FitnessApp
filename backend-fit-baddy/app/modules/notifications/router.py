from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.notifications import schemas, service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[schemas.NotificationOut])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.list_notifications(db, current_user.id)


@router.post("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = service.get_notification(db, current_user.id, notification_id)
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    note = service.mark_read(db, note)
    db.commit()
    db.refresh(note)
    return note
