"""
Слой бизнес-логики модуля. Роутер не должен напрямую лазить в БД мимо этого файла
(кроме простых случаев) — так проще тестировать и переиспользовать логику.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from . import models, schemas


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    user = models.User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
