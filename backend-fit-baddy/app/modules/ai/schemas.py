from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


DISCLAIMER = "This is not medical advice. Recommendations are informational only."

Intensity = Literal["light", "moderate", "hard"]


class SourceOut(BaseModel):
    id: str
    title: str
    url: str | None = None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    disclaimer: str = DISCLAIMER
    reason: str | None = None
    intensity: Intensity | None = None
    sources: list[SourceOut] = Field(default_factory=list)
    engine: str = "rules"

    @computed_field
    @property
    def recommendation(self) -> str:
        return self.text


class AskIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class AskOut(BaseModel):
    answer: str
    sources: list[SourceOut] = Field(default_factory=list)
    model: str | None = None
    disclaimer: str = DISCLAIMER


class AiStatusOut(BaseModel):
    engine: str
    rag_configured: bool
    rag_available: bool
    model: str | None = None


# Ответы RAG-сервиса в Colab (контракт — docs/ai/README.md)
class RagRecommendation(BaseModel):
    recommendation: str
    reason: str
    intensity: Intensity | None = None
    sources: list[SourceOut] = Field(default_factory=list)
    model: str | None = None


class RagAnswer(BaseModel):
    answer: str
    sources: list[SourceOut] = Field(default_factory=list)
    model: str | None = None
