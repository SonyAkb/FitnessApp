from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    xp: int
    xp_to_next_level: int
    level: int
    energy: int
    mood: str
    streak_days: int
    last_activity_date: date | None = None
    days_since_last_activity: int = 0
    updated_at: datetime | None = None

class QuestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    description: str | None = None
    period: str
    progress: int
    target: int
    xp_reward: int
    status: str
    deadline: datetime | None = None
    completed_at: datetime | None = None


class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    description: str | None = None
    xp_reward: int
    earned_at: datetime


class PetEventOut(BaseModel):
    """Событие журнала `pet_events` (PET-09)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: int
    xp_total: int
    level: int
    mood: str | None = None
    created_at: datetime


class PetStatsOut(BaseModel):
    weekly_xp: int