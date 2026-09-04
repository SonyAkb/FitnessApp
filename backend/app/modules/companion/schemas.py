from datetime import datetime
from pydantic import BaseModel


class CompanionRead(BaseModel):
    id: int
    name: str
    level: int
    energy: int
    mood: str
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementRead(BaseModel):
    id: int
    code: str
    unlocked_at: datetime

    class Config:
        from_attributes = True
