from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import settings
from app.modules.ai import models, rag_client
from app.modules.ai.schemas import DISCLAIMER
from app.modules.auth.models import User
from app.modules.workouts import service as workouts_service

RULES_REASON = "Rule-based suggestion from your recent workout history"
FITNESS_LEVELS = {"beginner", "intermediate", "advanced"}


@dataclass
class Advice:
    text: str
    reason: str
    engine: str
    intensity: str | None = None
    sources: list[dict] = field(default_factory=list)


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


def _aware(value: datetime) -> datetime:
    # SQLite отдаёт даты без часового пояса
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def history_summary(db: Session, user: User) -> dict:
    """Сводка для RAG-сервиса. Имя, email и id пользователя в неё не входят."""
    now = utc_now()
    done = [
        s for s in workouts_service.list_history(db, user.id, limit=50)
        if s.status == "completed" and s.completed_at is not None
    ]
    done.sort(key=lambda s: _aware(s.completed_at), reverse=True)
    profile = user.profile
    level = (profile.fitness_level or "").lower() if profile else ""
    recent = []
    if done and done[0].plan is not None:
        recent = [
            {"name": ex.name, "sets": ex.sets, "reps": ex.reps, "weight_kg": ex.weight_kg}
            for ex in done[0].plan.exercises[:10]
        ]
    return {
        "goal": profile.goal if profile else None,
        "fitness_level": level if level in FITNESS_LEVELS else None,
        "completed_7d": sum(_aware(s.completed_at) >= now - timedelta(days=7) for s in done),
        "completed_30d": sum(_aware(s.completed_at) >= now - timedelta(days=30) for s in done),
        "days_since_last": (now - _aware(done[0].completed_at)).days if done else None,
        "recent_workouts": recent,
    }


def rules_advice(db: Session, user_id: int) -> Advice:
    return Advice(text=rule_based_text(workouts_service.count_completed(db, user_id)), reason=RULES_REASON, engine="rules")


def rag_advice(db: Session, user: User) -> Advice:
    answer = rag_client.recommend(history_summary(db, user))
    return Advice(
        text=answer.recommendation,
        reason=answer.reason,
        engine="rag",
        intensity=answer.intensity,
        sources=[s.model_dump() for s in answer.sources],
    )


def get_advice(db: Session, user: User) -> Advice:
    if settings.AI_ENGINE == "rag":
        try:
            return rag_advice(db, user)
        except rag_client.RagUnavailable:
            pass  # Colab выключен или не ответил — рекомендация на правилах
    return rules_advice(db, user.id)


def create_recommendation(db: Session, user: User) -> models.Recommendation:
    advice = get_advice(db, user)
    rec = models.Recommendation(
        user_id=user.id,
        text=advice.text,
        reason=advice.reason,
        intensity=advice.intensity,
        sources=advice.sources,
        engine=advice.engine,
    )
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
