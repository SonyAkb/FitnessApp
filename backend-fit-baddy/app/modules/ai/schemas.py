from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


DISCLAIMER = "This is not medical advice. Recommendations are informational only."


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    disclaimer: str = DISCLAIMER
    reason: str | None = None

    @computed_field
    @property
    def recommendation(self) -> str:
        return self.text
