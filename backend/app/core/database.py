"""
Подключение к БД и базовый declarative класс для моделей всех модулей.
Каждый модуль импортирует Base отсюда для своих SQLAlchemy-моделей.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: сессия БД на один запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
