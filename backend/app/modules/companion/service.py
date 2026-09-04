from sqlalchemy.orm import Session
from . import models


def get_or_create_companion(db: Session, user_id: int) -> models.Companion:
    companion = db.query(models.Companion).filter(models.Companion.user_id == user_id).first()
    if not companion:
        companion = models.Companion(user_id=user_id)
        db.add(companion)
        db.commit()
        db.refresh(companion)
    return companion


def feed_companion(db: Session, user_id: int, energy_delta: int = 15) -> models.Companion:
    """
    Вызывается модулем training после завершения тренировки (см. TODO в training/router.py).
    TODO(module-3): продумать полноценную формулу роста/деградации, привязку к целям,
    апгрейд уровня, разблокировку достижений (Achievement).
    """
    companion = get_or_create_companion(db, user_id)
    companion.energy = min(100, companion.energy + energy_delta)
    companion.mood = "happy" if companion.energy > 70 else "neutral" if companion.energy > 30 else "sad"
    db.commit()
    db.refresh(companion)
    return companion
