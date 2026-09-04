from datetime import datetime
from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    sets: int = 3
    reps: int = 10
    weight_kg: float | None = None
    order_index: int = 0


class ExerciseRead(ExerciseCreate):
    id: int

    class Config:
        from_attributes = True


class WorkoutPlanCreate(BaseModel):
    name: str
    description: str | None = None
    exercises: list[ExerciseCreate] = []


class WorkoutPlanRead(BaseModel):
    id: int
    name: str
    description: str | None
    exercises: list[ExerciseRead] = []

    class Config:
        from_attributes = True


class WorkoutSessionRead(BaseModel):
    id: int
    plan_id: int | None
    started_at: datetime
    completed_at: datetime | None
    status: str

    class Config:
        from_attributes = True
