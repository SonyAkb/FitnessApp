from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.users_schedule.models import User
from . import schemas, service

router = APIRouter(prefix="/companion", tags=["companion"])


@router.get("/me", response_model=schemas.CompanionRead)
def get_my_companion(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.get_or_create_companion(db, current_user.id)


@router.post("/interact", response_model=schemas.CompanionRead)
def interact(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Заглушка ручного взаимодействия (погладить питомца и т.п.) — небольшой бонус к energy."""
    return service.feed_companion(db, current_user.id, energy_delta=5)
