from sqlalchemy.orm import Session

from app.modules.notifications import models


def create_notification(
    db: Session, user_id: int, title: str, body: str, kind: str | None = None
) -> models.Notification:
    note = models.Notification(user_id=user_id, title=title, body=body, kind=kind, is_read=False)
    db.add(note)
    db.flush()
    return note


def list_notifications(db: Session, user_id: int) -> list[models.Notification]:
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


def get_notification(db: Session, user_id: int, note_id: int) -> models.Notification | None:
    return (
        db.query(models.Notification)
        .filter(models.Notification.id == note_id, models.Notification.user_id == user_id)
        .first()
    )


def mark_read(db: Session, note: models.Notification) -> models.Notification:
    note.is_read = True
    db.flush()
    return note
