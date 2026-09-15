from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.ai import schemas, service
from app.modules.auth.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


def _out(rec) -> schemas.RecommendationOut:
    return schemas.RecommendationOut(
        id=rec.id,
        text=rec.text,
        created_at=rec.created_at,
        reason="Rule-based suggestion from your recent workout history",
    )


@router.get("/recommend", response_model=schemas.RecommendationOut)
def recommend(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = service.create_recommendation(db, current_user.id)
    db.commit()
    db.refresh(rec)
    return _out(rec)


@router.get("/history", response_model=list[schemas.RecommendationOut])
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_out(rec) for rec in service.list_history(db, current_user.id)]

