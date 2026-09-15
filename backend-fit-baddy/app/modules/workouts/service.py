from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.modules.workouts import models, schemas


def list_plans(db: Session, user_id: int) -> list[models.WorkoutPlan]:
    return (
        db.query(models.WorkoutPlan)
        .filter(models.WorkoutPlan.user_id == user_id)
        .order_by(models.WorkoutPlan.id)
        .all()
    )


def get_plan(db: Session, user_id: int, plan_id: int) -> models.WorkoutPlan | None:
    return (
        db.query(models.WorkoutPlan)
        .filter(models.WorkoutPlan.id == plan_id, models.WorkoutPlan.user_id == user_id)
        .first()
    )


def create_plan(db: Session, user_id: int, data: schemas.WorkoutPlanCreateIn) -> models.WorkoutPlan:
    plan = models.WorkoutPlan(user_id=user_id, title=data.resolved_title, description=data.description)
    for ex in data.exercises:
        plan.exercises.append(models.WorkoutPlanExercise(**ex.model_dump()))
    db.add(plan)
    db.flush()
    return plan


def start_session(
    db: Session, user_id: int, workout_plan_id: int, scheduled_id: int | None = None
) -> models.WorkoutSession:
    session = models.WorkoutSession(
        user_id=user_id,
        workout_plan_id=workout_plan_id,
        scheduled_id=scheduled_id,
        status="in_progress",
    )
    db.add(session)
    db.flush()
    return session


def get_session(db: Session, user_id: int, session_id: int) -> models.WorkoutSession | None:
    return (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.id == session_id, models.WorkoutSession.user_id == user_id)
        .first()
    )


def complete_session(
    db: Session, session: models.WorkoutSession, duration_seconds: int | None
) -> models.WorkoutSession:
    completed_at = utc_now()
    started = session.started_at
    if duration_seconds is None:
        if started.tzinfo is None:
            from datetime import timezone

            started = started.replace(tzinfo=timezone.utc)
        duration_seconds = max(0, int((completed_at - started).total_seconds()))
    session.status = "completed"
    session.completed_at = completed_at
    session.duration_seconds = duration_seconds
    session.xp_awarded = 25
    db.flush()
    return session


def list_history(db: Session, user_id: int) -> list[models.WorkoutSession]:
    return (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.user_id == user_id)
        .order_by(models.WorkoutSession.started_at.desc())
        .all()
    )


def count_completed(db: Session, user_id: int) -> int:
    return (
        db.query(models.WorkoutSession)
        .filter(
            models.WorkoutSession.user_id == user_id,
            models.WorkoutSession.status == "completed",
        )
        .count()
    )


def count_all(db: Session, user_id: int) -> int:
    return db.query(models.WorkoutSession).filter(models.WorkoutSession.user_id == user_id).count()


def plan_out(plan: models.WorkoutPlan) -> schemas.WorkoutPlanOut:
    return schemas.WorkoutPlanOut(
        id=plan.id,
        title=plan.title,
        name=plan.title,
        description=plan.description,
        exercises=[schemas.ExerciseOut.model_validate(ex) for ex in plan.exercises],
    )


def session_out(session: models.WorkoutSession) -> schemas.WorkoutSessionOut:
    plan_name = session.plan.title if session.plan is not None else None
    return schemas.WorkoutSessionOut(
        id=session.id,
        workout_plan_id=session.workout_plan_id,
        plan_id=session.workout_plan_id,
        scheduled_id=session.scheduled_id,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        duration_seconds=session.duration_seconds,
        xp_awarded=session.xp_awarded,
        plan_name=plan_name,
    )


def history_out(db: Session, user_id: int) -> schemas.WorkoutHistoryOut:
    rows = list_history(db, user_id)
    return schemas.WorkoutHistoryOut(
        items=[session_out(row) for row in rows],
        total=len(rows),
    )
