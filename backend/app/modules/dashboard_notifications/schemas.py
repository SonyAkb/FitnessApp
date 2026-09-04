from datetime import datetime
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    title: str
    body: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    title: str
    body: str | None = None


class DashboardSummary(BaseModel):
    total_workouts: int
    completed_workouts: int
    current_streak_days: int
    companion_mood: str | None = None
