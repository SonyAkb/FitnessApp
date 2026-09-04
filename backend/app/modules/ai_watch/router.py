from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.users_schedule.models import User
from app.modules.training.models import WorkoutSession
from . import models, schemas, watch_emulator, ai_recommender

router = APIRouter(tags=["ai & watch emulator"])


# ---------------------- WATCH EMULATOR ----------------------
@router.post("/watch/simulate", response_model=schemas.WatchDataPointRead, status_code=201)
def simulate_watch_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = watch_emulator.generate_data_point()
    point = models.WatchDataPoint(user_id=current_user.id, **data)
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


@router.get("/watch/latest", response_model=schemas.WatchDataPointRead | None)
def latest_watch_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(models.WatchDataPoint)
        .filter(models.WatchDataPoint.user_id == current_user.id)
        .order_by(models.WatchDataPoint.recorded_at.desc())
        .first()
    )


# ---------------------- AI RECOMMENDATION ----------------------
@router.get("/ai/recommend", response_model=schemas.RecommendationRead)
def get_recommendation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recent_completed = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == current_user.id, WorkoutSession.status == "completed")
        .count()
    )
    return ai_recommender.rule_based_recommend(recent_completed)
