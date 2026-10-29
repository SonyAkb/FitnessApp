from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.pet import schemas, service

router = APIRouter(tags=["pet"])


@router.get("/pet", response_model=schemas.PetOut)
def get_pet(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pet = service.get_or_create_pet(db, current_user.id)
    service.refresh_mood(db, pet)
    db.commit()
    db.refresh(pet)
    return service.pet_out(pet)

@router.get("/pet/quests", response_model=list[schemas.QuestOut])
def get_quests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = service.list_user_quests(db, current_user.id)
    db.commit()
    return [service.quest_out(row) for row in rows]


@router.get("/pet/achievements", response_model=list[schemas.AchievementOut])
def get_achievements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = service.list_user_achievements(db, current_user.id)
    db.commit()
    return [service.achievement_out(row) for row in rows]


@router.get("/pet/events", response_model=list[schemas.PetEventOut])
def get_pet_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История событий питомца (PET-09): xp, level_up, mood, return_bonus."""
    service.get_or_create_pet(db, current_user.id)
    db.commit()
    return service.list_events(db, current_user.id, limit=min(max(limit, 1), 200))


@router.get("/pet/stats", response_model=schemas.PetStatsOut)
def get_pet_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Статистика «сколько XP за неделю» по журналу pet_events (PET-09)."""
    return schemas.PetStatsOut(weekly_xp=service.weekly_xp(db, current_user.id))