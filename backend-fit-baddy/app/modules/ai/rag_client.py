"""HTTP-клиент LLM + RAG-сервиса в Google Colab (контракт — docs/ai/README.md)."""
import logging

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.modules.ai import schemas

log = logging.getLogger(__name__)

# Тесты подставляют httpx.MockTransport; в работе — обычный сетевой транспорт.
transport: httpx.BaseTransport | None = None


class RagUnavailable(Exception):
    """Сервис не настроен, не ответил вовремя или вернул ошибку."""


def is_configured() -> bool:
    return bool(settings.AI_RAG_URL)


def _request(method: str, path: str, payload: dict | None = None, timeout: float | None = None) -> dict:
    if not is_configured():
        raise RagUnavailable("AI_RAG_URL is not set")
    headers = {"X-AI-Token": settings.AI_RAG_TOKEN, "ngrok-skip-browser-warning": "1"}
    try:
        with httpx.Client(
            base_url=settings.AI_RAG_URL.rstrip("/"),
            headers=headers,
            timeout=timeout or settings.AI_RAG_TIMEOUT_S,
            transport=transport,
        ) as client:
            response = client.request(method, path, json=payload)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("RAG service unavailable: %s %s: %s", method, path, exc)
        raise RagUnavailable(str(exc)) from exc


def recommend(summary: dict) -> schemas.RagRecommendation:
    data = _request("POST", "/v1/recommend", summary)
    try:
        return schemas.RagRecommendation.model_validate(data)
    except ValidationError as exc:
        raise RagUnavailable(f"unexpected response: {exc}") from exc


def ask(question: str) -> schemas.RagAnswer:
    data = _request("POST", "/v1/ask", {"question": question})
    try:
        return schemas.RagAnswer.model_validate(data)
    except ValidationError as exc:
        raise RagUnavailable(f"unexpected response: {exc}") from exc


def health() -> dict:
    return _request("GET", "/health", timeout=5)
