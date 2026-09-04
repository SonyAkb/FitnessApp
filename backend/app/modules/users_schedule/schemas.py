from datetime import datetime
from pydantic import BaseModel, EmailStr


# ---- Auth / User ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    goal: str | None
    weight_kg: float | None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    weight_kg: float | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Schedule ----
class ScheduleEventCreate(BaseModel):
    title: str
    starts_at: datetime
    ends_at: datetime | None = None
    repeat_rule: str | None = None


class ScheduleEventRead(ScheduleEventCreate):
    id: int

    class Config:
        from_attributes = True
