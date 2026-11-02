from datetime import timezone

from fastapi import HTTPException
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.modules.workouts import models, schemas


def list_plans(db: Session, user_id: int) -> list[models.WorkoutPlan]:
    return (
        db.query(models.WorkoutPlan)
        .filter(models.WorkoutPlan.user_id == user_id, models.WorkoutPlan.archived_at.is_(None))
        .order_by(models.WorkoutPlan.id)
        .all()
    )


def get_plan(db: Session, user_id: int, plan_id: int) -> models.WorkoutPlan | None:
    return (
        db.query(models.WorkoutPlan)
        .filter(
            models.WorkoutPlan.id == plan_id,
            models.WorkoutPlan.user_id == user_id,
            models.WorkoutPlan.archived_at.is_(None),
        )
        .first()
    )


def update_plan(db: Session, plan: models.WorkoutPlan, data: schemas.WorkoutPlanUpdateIn) -> models.WorkoutPlan:
    if data.resolved_title:
        plan.title = data.resolved_title
    if "description" in data.model_fields_set:
        plan.description = data.description
    if data.exercises is not None:
        plan.exercises.clear()
        db.flush()
        for ex in data.exercises:
            plan.exercises.append(models.WorkoutPlanExercise(**ex.model_dump()))
    db.flush()
    return plan


def archive_plan(db: Session, plan: models.WorkoutPlan) -> None:
    plan.archived_at = utc_now()
    db.flush()


def create_plan(db: Session, user_id: int, data: schemas.WorkoutPlanCreateIn) -> models.WorkoutPlan:
    plan = models.WorkoutPlan(user_id=user_id, title=data.resolved_title, description=data.description)
    for ex in data.exercises:
        plan.exercises.append(models.WorkoutPlanExercise(**ex.model_dump()))
    db.add(plan)
    db.flush()
    return plan


def start_session(
    db: Session, user_id: int, plan: models.WorkoutPlan, scheduled_id: int | None = None
) -> models.WorkoutSession:
    session = models.WorkoutSession(
        user_id=user_id,
        workout_plan_id=plan.id,
        scheduled_id=scheduled_id,
        status="in_progress",
    )
    db.add(session)
    for ex in plan.exercises:
        se = models.WorkoutSessionExercise(
            exercise_id=ex.exercise_id, name=ex.name, order_index=ex.order_index
        )
        for i in range(1, ex.sets + 1):
            se.sets.append(models.ExerciseSet(
                set_index=i, target_reps=ex.reps, target_weight_kg=ex.weight_kg
            ))
        session.exercises.append(se)
    db.flush()
    return session


def get_session(db: Session, user_id: int, session_id: int) -> models.WorkoutSession | None:
    return (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.id == session_id, models.WorkoutSession.user_id == user_id)
        .first()
    )


def log_set(db: Session, user_id: int, session_id: int, data: schemas.SetLogIn) -> models.ExerciseSet:
    session = get_session(db, user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workout session not found")
    
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Session already completed")

    se = db.query(models.WorkoutSessionExercise).filter(
        models.WorkoutSessionExercise.id == data.session_exercise_id,
        models.WorkoutSessionExercise.session_id == session.id
    ).first()
    if not se:
        raise HTTPException(status_code=404, detail="Session exercise not found")

    target_set = db.query(models.ExerciseSet).filter(
        models.ExerciseSet.session_exercise_id == se.id,
        models.ExerciseSet.set_index == data.set_index
    ).first()
    if not target_set:
        raise HTTPException(status_code=404, detail="Exercise set not found")

    target_set.status = data.status
    if data.status == "done":
        target_set.actual_reps = data.actual_reps
        target_set.actual_weight_kg = data.actual_weight_kg
    else:  # skipped: фактических данных нет
        target_set.actual_reps = None
        target_set.actual_weight_kg = None
    target_set.completed_at = utc_now()

    all_sets = se.sets
    if not any(s.status == "pending" for s in all_sets):
        se.status = "done" if any(s.status == "done" for s in all_sets) else "skipped"
    else:
        se.status = "pending"

    db.flush()
    return target_set


def complete_session(
    db: Session, session: models.WorkoutSession, duration_seconds: int | None
) -> models.WorkoutSession:
    completed_at = utc_now()
    started = session.started_at
    if duration_seconds is None:
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        duration_seconds = max(0, int((completed_at - started).total_seconds()))
    session.status = "completed"
    session.completed_at = completed_at
    session.duration_seconds = duration_seconds
    session.xp_awarded = 25
    
    for se in session.exercises:
        for s in se.sets:
            if s.status == "pending":
                s.status = "skipped"
        se.status = "done" if any(s.status == "done" for s in se.sets) else "skipped"
        
    db.flush()
    return session


def list_history(
    db: Session, user_id: int, limit: int = 20, offset: int = 0
) -> list[models.WorkoutSession]:
    return (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.user_id == user_id)
        .order_by(models.WorkoutSession.started_at.desc(), models.WorkoutSession.id.desc())
        .offset(offset)
        .limit(limit)
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


def session_out(
    session: models.WorkoutSession, 
    metrics_map: dict | None = None, 
    include_exercises: bool = True
) -> schemas.WorkoutSessionOut:
    plan_name = session.plan.title if session.plan is not None else None
    
    if metrics_map is not None:
        # история: метрики посчитаны одним запросом; сессии без подходов -> нули
        sets_done, volume_kg = metrics_map.get(session.id, (0, 0.0))
    else:
        sets_done = 0
        volume_kg = 0.0
        for se in session.exercises:
            for s in se.sets:
                if s.status == "done":
                    sets_done += 1
                    if s.actual_reps is not None and s.actual_weight_kg is not None:
                        volume_kg += float(s.actual_reps * s.actual_weight_kg)

    exercises_out = None
    if include_exercises:
        exercises_out = [schemas.SessionExerciseOut.model_validate(se) for se in session.exercises]

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
        sets_done=sets_done,
        volume_kg=volume_kg,
        exercises=exercises_out,
    )


def history_out(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> schemas.WorkoutHistoryOut:
    rows = list_history(db, user_id, limit=limit, offset=offset)
    if not rows:
        return schemas.WorkoutHistoryOut(items=[], total=count_all(db, user_id))

    session_ids = [row.id for row in rows]
    metrics_query = (
        db.query(
            models.WorkoutSessionExercise.session_id,
            func.sum(
                case(
                    (models.ExerciseSet.status == "done", 1),
                    else_=0
                )
            ).label("sets_done"),
            func.sum(
                case(
                    (
                        (models.ExerciseSet.status == "done") & (models.ExerciseSet.actual_weight_kg.isnot(None)),
                        models.ExerciseSet.actual_reps * models.ExerciseSet.actual_weight_kg
                    ),
                    else_=0
                )
            ).label("volume_kg")
        )
        .join(models.ExerciseSet, models.ExerciseSet.session_exercise_id == models.WorkoutSessionExercise.id)
        .filter(models.WorkoutSessionExercise.session_id.in_(session_ids))
        .group_by(models.WorkoutSessionExercise.session_id)
        .all()
    )

    metrics_map = {row.session_id: (int(row.sets_done or 0), float(row.volume_kg or 0.0)) for row in metrics_query}

    return schemas.WorkoutHistoryOut(
        items=[session_out(row, metrics_map=metrics_map, include_exercises=False) for row in rows],
        total=count_all(db, user_id),
    )


def search_exercises(
    db: Session,
    q: str | None = None,
    muscle_group: schemas.MuscleGroup | None = None,
) -> list[models.Exercise]:
    query = db.query(models.Exercise)
    if muscle_group is not None:
        query = query.filter(models.Exercise.muscle_group == muscle_group.value)
    rows = query.order_by(models.Exercise.name).all()
    if q and q.strip():
        needle = q.strip().casefold()
        rows = [row for row in rows if needle in row.name.casefold()]
    return rows


def find_missing_exercise_ids(db: Session, exercises) -> list[int]:
    ids = {ex.exercise_id for ex in exercises if ex.exercise_id is not None}
    if not ids:
        return []
    found = {
        row[0] for row in db.query(models.Exercise.id).filter(models.Exercise.id.in_(ids)).all()
    }
    return sorted(ids - found)