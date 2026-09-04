"""
Модуль 3: Виртуальный персонаж (геймификация).
Владелец: <впишите имя ответственного>
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.core.database import Base


class Companion(Base):
    __tablename__ = "companions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, default="Спортик")
    level = Column(Integer, default=1)
    energy = Column(Integer, default=50)   # 0..100
    mood = Column(String, default="neutral")  # sad | neutral | happy | excited
    updated_at = Column(DateTime, default=datetime.utcnow)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)   # например: "streak_3_days"
    unlocked_at = Column(DateTime, default=datetime.utcnow)
