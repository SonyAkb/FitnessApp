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
