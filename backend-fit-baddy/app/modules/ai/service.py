from sqlalchemy.orm import Session

from app.modules.ai import models
from app.modules.ai.schemas import DISCLAIMER
from app.modules.workouts.service import count_completed


def rule_based_text(completed_count: int) -> str:
    if completed_count == 0:
        return (
            "Try a light full-body session today: bodyweight squats, push-ups, and a short walk. "
            f"{DISCLAIMER}"
        )
    if completed_count < 3:
        return (
            "Try increasing squat weight by 2.5 kg on your next strength day, "
            "and keep rest between sets around 90 seconds. "
            f"{DISCLAIMER}"
        )
    return (
        "Nice consistency. Consider adding 5 minutes of easy cardio after lifting, "
        "or take a recovery day if you feel sore. "
        f"{DISCLAIMER}"
    )


def create_recommendation(db: Session, user_id: int) -> models.Recommendation:
    completed = count_completed(db, user_id)
    rec = models.Recommendation(user_id=user_id, text=rule_based_text(completed))
    db.add(rec)
    db.flush()
    return rec


def list_history(db: Session, user_id: int) -> list[models.Recommendation]:
    return (
        db.query(models.Recommendation)
        .filter(models.Recommendation.user_id == user_id)
        .order_by(models.Recommendation.created_at.desc())
        .all()
    )
