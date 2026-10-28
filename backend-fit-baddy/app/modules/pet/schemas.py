from datetime import datetime

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