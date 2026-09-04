from datetime import datetime
from pydantic import BaseModel


class WatchDataPointRead(BaseModel):
    id: int
    steps: int
    heart_rate: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class RecommendationRead(BaseModel):
    recommendation: str
    reason: str
