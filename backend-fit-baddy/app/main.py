from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.events import register_event_handlers

from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.workouts import models as workout_models  # noqa: F401

from app.modules.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # MVP: tables are created from SQLAlchemy models.
    # Alembic is not used yet; switch to migrations when the schema stabilizes.
    Base.metadata.create_all(bind=engine)
    register_event_handlers()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="FitQuest educational MVP API for the Android client and telemetry simulator.",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=False if origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


app.include_router(auth_router, prefix="/api/v1")
