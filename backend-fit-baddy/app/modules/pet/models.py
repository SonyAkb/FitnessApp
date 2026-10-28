from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint

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
    mood = Column(String, nullable=False, default="idle")
    streak_days = Column(Integer, nullable=False, default=0)
    last_activity_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Quest(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    period = Column(String, nullable=False)
    target = Column(Integer, nullable=False, default=1)
    xp_reward = Column(Integer, nullable=False, default=0)


class UserQuest(Base):
    __tablename__ = "user_quests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False, index=True)
    progress = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notified = Column(Boolean, nullable=False, default=False)
    last_counted_at = Column(DateTime(timezone=True), nullable=True)
    completions = Column(Integer, nullable=False, default=0, server_default="0")


class Achievement(Base):
    """Справочник достижений (заполняется миграцией 0002, PET-07)."""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    xp_reward = Column(Integer, nullable=False, default=0)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)
    earned_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)