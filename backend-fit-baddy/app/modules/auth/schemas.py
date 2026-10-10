from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

# A slot may start slightly in the past: the client sends "now" and the request takes time.
SCHEDULE_PAST_GRACE = timedelta(minutes=15)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _require_not_past(value: datetime | None) -> datetime | None:
    if value is not None and _as_utc(value) < datetime.now(timezone.utc) - SCHEDULE_PAST_GRACE:
        raise ValueError("start time must not be in the past")
    return value


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
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("password")
    @classmethod
    def letters_and_digits(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
            raise ValueError("password must contain letters and digits")
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    goal: str | None = None
    weight_kg: float | None = Field(default=None, ge=30, le=300)
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
        _require_not_past(self.when)
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

    @model_validator(mode="after")
    def not_in_past(self):
        _require_not_past(self.planned_at)
        _require_not_past(self.starts_at)
        return self


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
