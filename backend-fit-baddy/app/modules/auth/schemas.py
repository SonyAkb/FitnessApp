from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    role: str
    goal: str | None = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal: str | None = None
    weight_kg: float | None = None
    fitness_level: str | None = None


class MeOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    role: str
    goal: str | None = None
    weight_kg: float | None = None
    fitness_level: str | None = None
    profile: ProfileOut


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    goal: str | None = None
    weight_kg: float | None = None
    fitness_level: str | None = None


class ScheduleCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    planned_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    workout_plan_id: int | None = None
    plan_id: int | None = None
    repeat_rule: str | None = None

    @model_validator(mode="after")
    def require_when(self):
        if self.planned_at is None and self.starts_at is None:
            raise ValueError("planned_at or starts_at is required")
        return self

    @property
    def when(self) -> datetime:
        return self.planned_at or self.starts_at  # type: ignore[return-value]

    @property
    def resolved_plan_id(self) -> int | None:
        return self.workout_plan_id if self.workout_plan_id is not None else self.plan_id


class ScheduleUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    planned_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    workout_plan_id: int | None = None
    plan_id: int | None = None
    repeat_rule: str | None = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    planned_at: datetime
    starts_at: datetime
    ends_at: datetime | None = None
    workout_plan_id: int | None
    plan_id: int | None
    repeat_rule: str | None
    status: str
    missed_at: datetime | None = None
