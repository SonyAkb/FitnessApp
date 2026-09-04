from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from . import models, schemas, service

router = APIRouter(tags=["users & schedule"])


# ---------------------- AUTH ----------------------
@router.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    return service.create_user(db, data)


@router.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token(subject=str(user.id))
    return schemas.Token(access_token=token)


# ---------------------- PROFILE ----------------------
@router.get("/profile/me", response_model=schemas.UserRead)
def read_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/profile/me", response_model=schemas.UserRead)
def update_profile(
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------- SCHEDULE ----------------------
@router.get("/schedule", response_model=list[schemas.ScheduleEventRead])
def list_schedule(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.user_id == current_user.id)
        .order_by(models.ScheduleEvent.starts_at)
        .all()
    )


@router.post("/schedule", response_model=schemas.ScheduleEventRead, status_code=status.HTTP_201_CREATED)
def create_schedule_event(
    data: schemas.ScheduleEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    event = models.ScheduleEvent(**data.model_dump(), user_id=current_user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/schedule/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    event = (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.id == event_id, models.ScheduleEvent.user_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    db.delete(event)
    db.commit()
