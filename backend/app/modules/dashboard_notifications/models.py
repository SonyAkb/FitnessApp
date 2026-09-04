"""
Модуль 5: Дашборды и уведомления.
Владелец: <впишите имя ответственного>
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationRule(Base):
    """Настройки уведомлений пользователя (когда/что присылать)."""
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)      # workout_reminder | companion_alert | achievement
    is_enabled = Column(Boolean, default=True)
    send_at = Column(String, nullable=True)    # например "08:00" — TODO: продумать формат/таймзоны
