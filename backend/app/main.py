"""
Точка входа FastAPI-приложения.
Здесь только "сборка": подключение роутеров всех модулей, CORS, создание таблиц.
Логику пишем в модулях (app/modules/<name>/), а не здесь.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

# Модели нужно импортировать до create_all(), иначе SQLAlchemy не узнает о таблицах
from app.modules.users_schedule import models as users_schedule_models  # noqa: F401
from app.modules.training import models as training_models              # noqa: F401
from app.modules.companion import models as companion_models            # noqa: F401
from app.modules.payments import models as payments_models              # noqa: F401
from app.modules.dashboard_notifications import models as dashboard_models  # noqa: F401
from app.modules.ai_watch import models as ai_watch_models               # noqa: F401

from app.modules.users_schedule.router import router as users_schedule_router
from app.modules.training.router import router as training_router
from app.modules.companion.router import router as companion_router
from app.modules.payments.router import router as payments_router
from app.modules.dashboard_notifications.router import router as dashboard_router
from app.modules.ai_watch.router import router as ai_watch_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # MVP: создаём таблицы из моделей напрямую.
    # TODO(всем): когда схема стабилизируется — перейти на Alembic-миграции,
    # чтобы изменения БД были версионированы и накатывались явно.
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


app.include_router(users_schedule_router)
app.include_router(training_router)
app.include_router(companion_router)
app.include_router(payments_router)
app.include_router(dashboard_router)
app.include_router(ai_watch_router)
