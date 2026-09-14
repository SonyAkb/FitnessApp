from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.events import WORKOUT_COMPLETED, event_bus
from app.modules.auth.models import User
from app.modules.workouts import schemas, service

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/plans", response_model=list[schemas.WorkoutPlanOut])
def list_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [service.plan_out(plan) for plan in service.list_plans(db, current_user.id)]


@router.post("/plans", response_model=schemas.WorkoutPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: schemas.WorkoutPlanCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = service.create_plan(db, current_user.id, data)
    db.commit()
    db.refresh(plan)
    return service.plan_out(plan)


@router.get("/plans/{plan_id}", response_model=schemas.WorkoutPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = service.get_plan(db, current_user.id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    return service.plan_out(plan)


@router.post("/sessions", response_model=schemas.WorkoutSessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    data: schemas.SessionStartIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = service.get_plan(db, current_user.id, data.resolved_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    session = service.start_session(
        db, current_user.id, data.resolved_plan_id, scheduled_id=data.scheduled_id
    )
    db.commit()
    db.refresh(session)
    return service.session_out(session)


@router.post("/sessions/{session_id}/complete", response_model=schemas.WorkoutSessionOut)
def complete_session(
    session_id: int,
    data: schemas.SessionCompleteIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = service.get_session(db, current_user.id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workout session not found")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Session already completed")
    body = data or schemas.SessionCompleteIn()
    session = service.complete_session(db, session, body.duration_seconds)
    db.commit()
    db.refresh(session)
    event_bus.publish(
        WORKOUT_COMPLETED,
        {
            "user_id": current_user.id,
            "session_id": session.id,
            "completed_at": session.completed_at,
            "duration_seconds": session.duration_seconds,
        },
        db,
    )
    db.commit()
    return service.session_out(session)


@router.get("/sessions/{session_id}", response_model=schemas.WorkoutSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = service.get_session(db, current_user.id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workout session not found")
    return service.session_out(session)


@router.get("/history", response_model=schemas.WorkoutHistoryOut)
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.history_out(db, current_user.id)
