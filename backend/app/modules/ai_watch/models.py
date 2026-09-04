"""
Модуль 6: ИИ-рекомендации + эмулятор умных часов.
Владелец: <впишите имя ответственного>
"""
from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from app.core.database import Base


class WatchDataPoint(Base):
    """Синтетическая точка данных 'умных часов' (шаги/пульс)."""
    __tablename__ = "watch_data_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    steps = Column(Integer, default=0)
    heart_rate = Column(Integer, default=70)
    recorded_at = Column(DateTime, default=datetime.utcnow)
