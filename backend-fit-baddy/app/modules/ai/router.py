from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.ai import rag_client, schemas, service
from app.modules.auth.models import User
from app.modules.subscription.service import can_use

router = APIRouter(prefix="/ai", tags=["ai"])


def _out(rec) -> schemas.RecommendationOut:
    return schemas.RecommendationOut(
        id=rec.id,
        text=rec.text,
        created_at=rec.created_at,
        reason=rec.reason or service.RULES_REASON,
        intensity=rec.intensity,
        sources=rec.sources or [],
        engine=rec.engine or "rules",
    )


def _require_pro(db: Session, user: User) -> None:
    if not can_use(db, user.id, "ai_recommendations"):
        raise HTTPException(status_code=403, detail="AI recommendations require the Pro plan")


@router.get("/recommend", response_model=schemas.RecommendationOut)
def recommend(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_pro(db, current_user)
    rec = service.create_recommendation(db, current_user)
    db.commit()
    db.refresh(rec)
    return _out(rec)


@router.get("/history", response_model=list[schemas.RecommendationOut])
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_out(rec) for rec in service.list_history(db, current_user.id)]


@router.post(
    "/ask",
    response_model=schemas.AskOut,
    responses={503: {"description": "AI assistant is disabled or the RAG service is unavailable"}},
)
def ask(body: schemas.AskIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_pro(db, current_user)
    if settings.AI_ENGINE != "rag":
        raise HTTPException(status_code=503, detail="AI assistant is disabled (AI_ENGINE=rules)")
    try:
        answer = rag_client.ask(body.question)
    except rag_client.RagUnavailable:
        raise HTTPException(status_code=503, detail="AI assistant is unavailable, try again later")
    return schemas.AskOut(answer=answer.answer, sources=answer.sources, model=answer.model)


@router.get("/status", response_model=schemas.AiStatusOut)
def status(current_user: User = Depends(get_current_user)):
    model, available = None, False
    if settings.AI_ENGINE == "rag" and rag_client.is_configured():
        try:
            model = rag_client.health().get("model")
            available = True
        except rag_client.RagUnavailable:
            pass
    return schemas.AiStatusOut(
        engine=settings.AI_ENGINE,
        rag_configured=rag_client.is_configured(),
        rag_available=available,
        model=model,
    )
