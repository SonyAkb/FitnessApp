from sqlalchemy.orm import Session

from app.modules.auth import service as auth_service
from app.modules.dashboard.schemas import DashboardSummaryOut
from app.modules.devices import service as devices_service
from app.modules.pet import service as pet_service
from app.modules.workouts import service as workouts_service

_MOOD_ANDROID = {"idle": "neutral", "level_up": "happy"}


def get_summary(db: Session, user_id: int) -> DashboardSummaryOut:
    pet = pet_service.get_or_create_pet(db, user_id)
    latest = devices_service.get_latest(db, user_id)
    today = auth_service.list_today_schedule(db, user_id)
    completed = workouts_service.count_completed(db, user_id)
    total = workouts_service.count_all(db, user_id)
    missed = auth_service.count_missed(db, user_id)
    companion = _MOOD_ANDROID.get(pet.mood, pet.mood)
    return DashboardSummaryOut(
        completed_workouts_count=completed,
        current_streak_days=pet.streak_days,
        xp=pet.xp,
        level=pet.level,
        mood=pet.mood,
        last_heart_rate=latest.heart_rate if latest else None,
        last_steps=latest.steps if latest else None,
        today_schedule=[auth_service.schedule_out(item) for item in today],
        period="week",
        total_workouts=total,
        completed_workouts=completed,
        missed_workouts=missed,
        companion_mood=companion,
        steps_7d=latest.steps if latest else None,
        workouts_by_day=[],
    )
