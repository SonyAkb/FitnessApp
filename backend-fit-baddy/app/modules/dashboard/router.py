from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.dashboard import schemas, service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=schemas.DashboardSummaryOut)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.get_summary(db, current_user.id)
