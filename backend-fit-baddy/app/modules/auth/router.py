from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.core.clock import utc_now
from app.events import USER_REGISTERED, WORKOUT_MISSED, event_bus
from app.modules.auth import models, schemas, service

router = APIRouter(tags=["auth & schedule"])


@router.post("/auth/register", response_model=schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")
    user = service.create_user(db, data)
    db.commit()
    db.refresh(user)
    event_bus.publish(USER_REGISTERED, {"user_id": user.id}, db)
    db.commit()
    return schemas.TokenOut(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
        user=service.user_out(user),
    )


@router.post("/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    return schemas.TokenOut(
        access_token=token,
        refresh_token=create_refresh_token(subject=str(user.id)),
        user=service.user_out(user),
    )


@router.get("/auth/me", response_model=schemas.MeOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return service.me_out(current_user)


@router.patch("/profile", response_model=schemas.MeOut)
def patch_profile(
    data: schemas.ProfileUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = service.update_profile(db, current_user, data)
    db.commit()
    db.refresh(user)
    return service.me_out(user)


@router.get("/schedule", response_model=list[schemas.ScheduleOut])
def list_schedule(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return [service.schedule_out(item) for item in service.list_schedule(db, current_user.id)]


@router.post("/schedule", response_model=schemas.ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: schemas.ScheduleCreateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    plan_id = data.resolved_plan_id
    if plan_id is not None:
        from app.modules.workouts.service import get_plan

        if not get_plan(db, current_user.id, plan_id):
            raise HTTPException(status_code=404, detail="Workout plan not found")
    item = service.create_schedule(db, current_user.id, data)
    db.commit()
    db.refresh(item)
    return service.schedule_out(item)


@router.patch("/schedule/{item_id}", response_model=schemas.ScheduleOut)
def update_schedule(
    item_id: int,
    data: schemas.ScheduleUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = service.get_schedule_item(db, current_user.id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    item = service.update_schedule(db, item, data)
    db.commit()
    db.refresh(item)
    return service.schedule_out(item)


@router.delete("/schedule/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = service.get_schedule_item(db, current_user.id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    db.delete(item)
    db.commit()


@router.post("/schedule/{item_id}/miss", response_model=schemas.ScheduleOut)
def miss_schedule(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = service.get_schedule_item(db, current_user.id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if item.status in {"missed", "completed"}:
        raise HTTPException(status_code=409, detail="Schedule item already marked missed")
    item.status = "missed"
    item.missed_at = utc_now()
    db.commit()
    db.refresh(item)
    event_bus.publish(
        WORKOUT_MISSED,
        {
            "user_id": current_user.id,
            "schedule_id": item.id,
            "scheduled_id": item.id,
            "title": item.title,
            "missed_at": item.missed_at,
        },
        db,
    )
    db.commit()
    return service.schedule_out(item)
