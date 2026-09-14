from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.clock import utc_now
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    schedule_items = relationship("ScheduledWorkout", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    goal = Column(String, nullable=True)
    weight_kg = Column(Float, nullable=True)
    fitness_level = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")


class ScheduledWorkout(Base):
    __tablename__ = "scheduled_workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    planned_at = Column(DateTime(timezone=True), nullable=False)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=True)
    repeat_rule = Column(String, nullable=True)
    status = Column(String, nullable=False, default="planned")  # planned | missed | completed
    ends_at = Column(DateTime(timezone=True), nullable=True)
    missed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="schedule_items")
