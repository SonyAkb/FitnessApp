from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.clock import utc_now
from app.core.database import Base


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    exercises = relationship(
        "WorkoutPlanExercise",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutPlanExercise.id",
    )
    sessions = relationship("WorkoutSession", back_populates="plan")


class WorkoutPlanExercise(Base):
    __tablename__ = "workout_plan_exercises"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    name = Column(String, nullable=False)
    sets = Column(Integer, nullable=False, default=3)
    reps = Column(Integer, nullable=False, default=10)
    weight_kg = Column(Float, nullable=True)
    rest_seconds = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)

    plan = relationship("WorkoutPlan", back_populates="exercises")


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    scheduled_id = Column(Integer, ForeignKey("scheduled_workouts.id"), nullable=True)
    status = Column(String, nullable=False, default="in_progress")  # in_progress | completed
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    xp_awarded = Column(Integer, nullable=True)

    plan = relationship("WorkoutPlan", back_populates="sessions")
