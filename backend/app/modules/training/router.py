"""
MVP-эндпоинты модуля. Реализованы базовые операции — этого достаточно,
чтобы фронт мог с чем-то работать. Дальше владелец модуля добавляет:
  - редактирование/удаление плана и упражнений
  - завершение сессии (complete_session) с расчётом длительности
  - интеграцию с модулем 3 (companion) — событие "тренировка завершена"
  - интеграцию с модулем 5 (notifications) — напоминания
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.users_schedule.models import User
from . import models, schemas

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/plans", response_model=list[schemas.WorkoutPlanRead])
def list_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_id == current_user.id).all()


@router.post("/plans", response_model=schemas.WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: schemas.WorkoutPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = models.WorkoutPlan(name=data.name, description=data.description, user_id=current_user.id)
    for ex in data.exercises:
        plan.exercises.append(models.Exercise(**ex.model_dump()))
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/start", response_model=schemas.WorkoutSessionRead, status_code=status.HTTP_201_CREATED)
def start_session(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = (
        db.query(models.WorkoutPlan)
        .filter(models.WorkoutPlan.id == plan_id, models.WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    session = models.WorkoutSession(user_id=current_user.id, plan_id=plan_id, status="in_progress")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/sessions/{session_id}/complete", response_model=schemas.WorkoutSessionRead)
def complete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.id == session_id, models.WorkoutSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    # TODO(module-3): дернуть companion-сервис, чтобы «покормить» персонажа
    # TODO(module-5): создать уведомление/обновить дашборд
    return session


@router.get("/sessions", response_model=list[schemas.WorkoutSessionRead])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.user_id == current_user.id)
        .order_by(models.WorkoutSession.started_at.desc())
        .all()
    )
