"""
MVP: базовый список уведомлений + заглушка дашборда, агрегирующая данные
из training (Модуль 2) и companion (Модуль 3).
TODO(module-5):
  - реальный расчёт current_streak_days
  - графики по весам/повторениям (нужны доп. данные из training — согласовать формат)
  - push-уведомления через Service Worker на фронте + APScheduler/cron на бэке
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.users_schedule.models import User
from app.modules.training.models import WorkoutSession
from app.modules.companion.service import get_or_create_companion
from . import models, schemas

router = APIRouter(tags=["dashboard & notifications"])


@router.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(WorkoutSession).filter(WorkoutSession.user_id == current_user.id).all()
    completed = [s for s in sessions if s.status == "completed"]
    companion = get_or_create_companion(db, current_user.id)
    return schemas.DashboardSummary(
        total_workouts=len(sessions),
        completed_workouts=len(completed),
        current_streak_days=0,  # TODO(module-5): реальная формула стрика
        companion_mood=companion.mood,
    )


@router.get("/notifications", response_model=list[schemas.NotificationRead])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@router.post("/notifications", response_model=schemas.NotificationRead)
def create_notification(
    data: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """MVP: ручное создание уведомления (для теста). В будущем — генерируется системой."""
    note = models.Notification(user_id=current_user.id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
