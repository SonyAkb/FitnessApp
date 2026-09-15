from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExerciseIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sets: int = Field(default=3, ge=1)
    reps: int = Field(default=10, ge=1)
    weight_kg: float | None = None
    rest_seconds: int | None = None
    order_index: int = 0


class ExerciseOut(ExerciseIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WorkoutPlanCreateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    exercises: list[ExerciseIn] = []

    @model_validator(mode="after")
    def require_title(self):
        if not (self.title or self.name):
            raise ValueError("title or name is required")
        return self

    @property
    def resolved_title(self) -> str:
        return self.title or self.name or "Workout"


class WorkoutPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    name: str
    description: str | None = None
    exercises: list[ExerciseOut] = []


class SessionStartIn(BaseModel):
    workout_plan_id: int | None = None
    plan_id: int | None = None
    scheduled_id: int | None = None

    @model_validator(mode="after")
    def require_plan(self):
        if self.workout_plan_id is None and self.plan_id is None:
            raise ValueError("workout_plan_id or plan_id is required")
        return self

    @property
    def resolved_plan_id(self) -> int:
        return int(self.workout_plan_id if self.workout_plan_id is not None else self.plan_id)


class SessionCompleteIn(BaseModel):
    duration_seconds: int | None = Field(default=None, ge=0)


class WorkoutSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_plan_id: int
    plan_id: int
    scheduled_id: int | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    xp_awarded: int | None = None
    plan_name: str | None = None


class WorkoutHistoryOut(BaseModel):
    items: list[WorkoutSessionOut]
    total: int
