import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("MOCK_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("TELEMETRY_WS_INTERVAL_SECONDS", "0.05")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


WEBHOOK_HEADERS = {"X-Mock-Signature": os.environ["MOCK_WEBHOOK_SECRET"]}


@pytest.fixture()
def db_session(client):
    """Database session for unit tests of services (tables are created by `client`)."""
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(client: TestClient, email: str = "demo@example.com", password: str = "secret12", name: str = "Demo"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["user"]


def create_plan(client: TestClient, headers: dict[str, str], title: str = "Legs") -> dict:
    response = client.post(
        "/api/v1/workouts/plans",
        json={"title": title, "exercises": [{"name": "Squat", "sets": 3, "reps": 10, "weight_kg": 40}]},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def complete_workout(client: TestClient, headers: dict[str, str], plan_id: int | None = None) -> dict:
    if plan_id is None:
        plan_id = create_plan(client, headers)["id"]
    session = client.post("/api/v1/workouts/sessions", json={"workout_plan_id": plan_id}, headers=headers)
    assert session.status_code == 201, session.text
    done = client.post(f"/api/v1/workouts/sessions/{session.json()['id']}/complete", json={}, headers=headers)
    assert done.status_code == 200, done.text
    return done.json()
