from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.auth import models, schemas


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, data: schemas.RegisterIn) -> models.User:
    user = models.User(
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
        role="user",
    )
    user.profile = models.Profile()
    db.add(user)
    db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def user_out(user: models.User) -> schemas.UserOut:
    goal = user.profile.goal if user.profile else None
    return schemas.UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        goal=goal,
    )


def me_out(user: models.User) -> schemas.MeOut:
    profile = user.profile or models.Profile(user_id=user.id)
    profile_out = schemas.ProfileOut.model_validate(profile)
    return schemas.MeOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        goal=profile_out.goal,
        weight_kg=profile_out.weight_kg,
        fitness_level=profile_out.fitness_level,
        profile=profile_out,
    )


def update_profile(db: Session, user: models.User, data: schemas.ProfileUpdateIn) -> models.User:
    payload = data.model_dump(exclude_unset=True)
    if "display_name" in payload and payload["display_name"] is not None:
        user.display_name = payload.pop("display_name")
    if user.profile is None:
        user.profile = models.Profile(user_id=user.id)
        db.add(user.profile)
    for field, value in payload.items():
        setattr(user.profile, field, value)
    db.flush()
    return user


def list_schedule(db: Session, user_id: int) -> list[models.ScheduledWorkout]:
    return (
        db.query(models.ScheduledWorkout)
        .filter(models.ScheduledWorkout.user_id == user_id)
        .order_by(models.ScheduledWorkout.planned_at)
        .all()
    )


def list_today_schedule(db: Session, user_id: int) -> list[models.ScheduledWorkout]:
    today = datetime.now(timezone.utc).date()
    items = list_schedule(db, user_id)
    result = []
    for item in items:
        planned = item.planned_at
        if planned.tzinfo is None:
            planned = planned.replace(tzinfo=timezone.utc)
        if planned.date() == today:
            result.append(item)
    return result


def count_missed(db: Session, user_id: int) -> int:
    return (
        db.query(models.ScheduledWorkout)
        .filter(models.ScheduledWorkout.user_id == user_id, models.ScheduledWorkout.status == "missed")
        .count()
    )


def get_schedule_item(db: Session, user_id: int, item_id: int) -> models.ScheduledWorkout | None:
    return (
        db.query(models.ScheduledWorkout)
        .filter(models.ScheduledWorkout.id == item_id, models.ScheduledWorkout.user_id == user_id)
        .first()
    )


def create_schedule(db: Session, user_id: int, data: schemas.ScheduleCreateIn) -> models.ScheduledWorkout:
    item = models.ScheduledWorkout(
        user_id=user_id,
        title=data.title,
        planned_at=data.when,
        workout_plan_id=data.resolved_plan_id,
        repeat_rule=data.repeat_rule,
        ends_at=data.ends_at,
        status="planned",
    )
    db.add(item)
    db.flush()
    return item


def update_schedule(
    db: Session, item: models.ScheduledWorkout, data: schemas.ScheduleUpdateIn
) -> models.ScheduledWorkout:
    payload = data.model_dump(exclude_unset=True)
    if "starts_at" in payload and "planned_at" not in payload:
        payload["planned_at"] = payload.pop("starts_at")
    else:
        payload.pop("starts_at", None)
    if "plan_id" in payload and "workout_plan_id" not in payload:
        payload["workout_plan_id"] = payload.pop("plan_id")
    else:
        payload.pop("plan_id", None)
    for field, value in payload.items():
        setattr(item, field, value)
    db.flush()
    return item


def schedule_out(item: models.ScheduledWorkout) -> schemas.ScheduleOut:
    return schemas.ScheduleOut(
        id=item.id,
        title=item.title,
        planned_at=item.planned_at,
        starts_at=item.planned_at,
        ends_at=item.ends_at,
        workout_plan_id=item.workout_plan_id,
        plan_id=item.workout_plan_id,
        repeat_rule=item.repeat_rule,
        status=item.status,
        missed_at=item.missed_at,
    )
