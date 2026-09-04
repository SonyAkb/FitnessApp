"""
Модуль 1: Пользователи, аутентификация, расписание тренировок.
Владелец: <впишите имя ответственного>
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    goal = Column(String, nullable=True)          # например: "weight_loss", "muscle_gain"
    weight_kg = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    schedule_events = relationship("ScheduleEvent", back_populates="owner", cascade="all, delete-orphan")


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    repeat_rule = Column(String, nullable=True)   # TODO: заготовка под RRULE-строку (повторяющиеся события)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="schedule_events")
