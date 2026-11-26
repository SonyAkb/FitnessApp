"""Module 5 — AI: LLM + RAG-сервис в Colab и откат на правила (AI-03, US-H2)."""
import json

import httpx
import pytest

from app.core.config import settings
from app.modules.ai import rag_client
from tests.conftest import auth_header, complete_workout, register_user

RAG_ANSWER = {
    "recommendation": "Сделайте присед 3×10 с весом 42 кг.",
    "intensity": "moderate",
    "reason": "Все подходы выполнены, прибавка в пределах 2–10%.",
    "sources": [{"id": "acsm-2009", "title": "Ratamess et al., 2009", "url": "https://doi.org/10.1249/MSS.0b013e3181915670"}],
    "model": "qwen3:8b",
    "disclaimer": "Это не медицинская рекомендация.",
}


@pytest.fixture()
def rag(monkeypatch):
    """Включает AI_ENGINE=rag и подменяет сеть: handler задаёт ответ Colab, requests — что пришло."""
    state = {"handler": lambda request: httpx.Response(200, json=RAG_ANSWER), "requests": []}

    def dispatch(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        return state["handler"](request)

    monkeypatch.setattr(settings, "AI_ENGINE", "rag")
    monkeypatch.setattr(settings, "AI_RAG_URL", "https://colab.example/")
    monkeypatch.setattr(settings, "AI_RAG_TOKEN", "test-ai-token")
    monkeypatch.setattr(rag_client, "transport", httpx.MockTransport(dispatch))
    return state


def pro_user(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    assert client.post("/api/v1/subscription/checkout", json={"plan": "pro"}, headers=headers).status_code == 200
    return headers


def test_rag_answer_is_returned_and_saved(client, rag):
    headers = pro_user(client)
    profile = client.patch("/api/v1/profile", json={"goal": "набрать массу", "fitness_level": "Beginner"}, headers=headers)
    assert profile.status_code == 200, profile.text
    complete_workout(client, headers)

    body = client.get("/api/v1/ai/recommend", headers=headers).json()
    assert body["engine"] == "rag"
    assert body["recommendation"] == RAG_ANSWER["recommendation"]
    assert body["intensity"] == "moderate"
    assert body["reason"] == RAG_ANSWER["reason"]
    assert body["sources"][0]["id"] == "acsm-2009"
    assert body["disclaimer"]

    history = client.get("/api/v1/ai/history", headers=headers).json()
    assert history[0]["engine"] == "rag" and history[0]["sources"] == body["sources"]

    request = rag["requests"][0]
    assert request.url == "https://colab.example/v1/recommend"
    assert request.headers["X-AI-Token"] == "test-ai-token"
    summary = json.loads(request.content)
    assert summary["completed_7d"] == 1 and summary["completed_30d"] == 1
    assert summary["days_since_last"] == 0
    assert summary["recent_workouts"][0]["name"] == "Squat"
    assert summary["goal"] == "набрать массу" and summary["fitness_level"] == "beginner"


def test_summary_has_no_personal_data(client, rag):
    headers = pro_user(client)
    client.get("/api/v1/ai/recommend", headers=headers)
    sent = rag["requests"][0].content.decode()
    assert "demo@example.com" not in sent and "Demo" not in sent
    assert set(json.loads(sent)) == {
        "goal", "fitness_level", "completed_7d", "completed_30d", "days_since_last", "recent_workouts",
    }


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timeout", request=request)),
        lambda request: httpx.Response(401, json={"detail": "invalid X-AI-Token"}),
        lambda request: httpx.Response(503, json={"detail": "LLM unavailable"}),
        lambda request: httpx.Response(200, json={"unexpected": True}),
        lambda request: httpx.Response(200, text="<html>ngrok warning</html>"),
    ],
    ids=["timeout", "401", "503", "bad-json-shape", "not-json"],
)
def test_falls_back_to_rules_when_rag_fails(client, rag, handler):
    rag["handler"] = handler
    headers = pro_user(client)
    response = client.get("/api/v1/ai/recommend", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "rules"
    assert body["recommendation"] and body["reason"] and body["disclaimer"]


def test_rag_engine_without_url_uses_rules(client, rag, monkeypatch):
    monkeypatch.setattr(settings, "AI_RAG_URL", "")
    headers = pro_user(client)
    assert client.get("/api/v1/ai/recommend", headers=headers).json()["engine"] == "rules"
    assert rag["requests"] == []


def test_rules_engine_does_not_call_colab(client, rag, monkeypatch):
    monkeypatch.setattr(settings, "AI_ENGINE", "rules")
    headers = pro_user(client)
    assert client.get("/api/v1/ai/recommend", headers=headers).json()["engine"] == "rules"
    assert rag["requests"] == []


def test_ask_returns_answer_with_sources(client, rag):
    rag["handler"] = lambda request: httpx.Response(
        200, json={"answer": "150–300 минут в неделю.", "sources": [{"id": "who-2020-ru", "title": "ВОЗ"}], "model": "qwen3:8b"}
    )
    headers = pro_user(client)
    response = client.post("/api/v1/ai/ask", json={"question": "Сколько нужно двигаться?"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("150") and body["sources"][0]["id"] == "who-2020-ru" and body["disclaimer"]
    assert rag["requests"][0].url.path == "/v1/ask"


def test_ask_is_503_when_rag_is_down_or_disabled(client, rag, monkeypatch):
    headers = pro_user(client)
    rag["handler"] = lambda request: httpx.Response(503)
    assert client.post("/api/v1/ai/ask", json={"question": "Сколько?"}, headers=headers).status_code == 503
    monkeypatch.setattr(settings, "AI_ENGINE", "rules")
    assert client.post("/api/v1/ai/ask", json={"question": "Сколько?"}, headers=headers).status_code == 503


def test_ask_requires_pro(client, rag):
    token, _ = register_user(client)
    response = client.post("/api/v1/ai/ask", json={"question": "Сколько?"}, headers=auth_header(token))
    assert response.status_code == 403


def test_status_reports_engine_and_availability(client, rag, monkeypatch):
    token, _ = register_user(client)
    headers = auth_header(token)
    rag["handler"] = lambda request: httpx.Response(200, json={"status": "ok", "model": "qwen3:8b"})
    assert client.get("/api/v1/ai/status", headers=headers).json() == {
        "engine": "rag", "rag_configured": True, "rag_available": True, "model": "qwen3:8b",
    }
    rag["handler"] = lambda request: httpx.Response(502)
    assert client.get("/api/v1/ai/status", headers=headers).json()["rag_available"] is False
    monkeypatch.setattr(settings, "AI_ENGINE", "rules")
    assert client.get("/api/v1/ai/status", headers=headers).json()["engine"] == "rules"
