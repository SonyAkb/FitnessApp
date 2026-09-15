from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String

from app.core.clock import utc_now
from app.core.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False, default="FitBuddy")
    xp = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    energy = Column(Integer, nullable=False, default=50)
    mood = Column(String, nullable=False, default="idle")  # idle | happy | sad | level_up | neutral
    streak_days = Column(Integer, nullable=False, default=0)
    last_activity_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
