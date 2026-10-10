"""Module 1 — registration, login, tokens and profile (US-A1, US-A2; AC1.x, AC2.1–2.2, AC-G1, AC-G3)."""
from datetime import timedelta

from jose import jwt

from app.core.clock import utc_now
from app.core.config import settings
from tests.conftest import auth_header, register_user


def register(client, email="new@example.com", password="secret12"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "New"},
    )


def test_register_creates_user_without_goal(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["goal"] is None


def test_register_duplicate_email_conflicts(client):
    register_user(client)
    response = register(client, email="demo@example.com")
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    assert register(client, password="abc12").status_code == 422


def test_register_rejects_password_without_digits_or_letters(client):
    assert register(client, password="onlyletters").status_code == 422
    assert register(client, email="d@example.com", password="12345678").status_code == 422


def test_register_rejects_invalid_email(client):
    assert register(client, email="not-an-email").status_code == 422


def test_login_with_wrong_password_is_unauthorized(client):
    register_user(client)
    response = client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "wrong123"})
    assert response.status_code == 401


def test_refresh_returns_new_tokens(client):
    body = register(client).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert response.status_code == 200
    me = client.get("/api/v1/auth/me", headers=auth_header(response.json()["access_token"]))
    assert me.status_code == 200


def test_refresh_rejects_access_token(client):
    body = register(client).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": body["access_token"]})
    assert response.status_code == 401


def test_refresh_token_is_not_accepted_as_access_token(client):
    body = register(client).json()
    response = client.get("/api/v1/auth/me", headers=auth_header(body["refresh_token"]))
    assert response.status_code == 401


def test_expired_access_token_is_unauthorized(client):
    _, user = register_user(client)
    expired = jwt.encode(
        {"sub": str(user["id"]), "typ": "access", "exp": utc_now() - timedelta(minutes=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert client.get("/api/v1/auth/me", headers=auth_header(expired)).status_code == 401


def test_profile_update_is_visible_in_me_and_not_reset(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    response = client.patch(
        "/api/v1/profile",
        json={"goal": "weight_loss", "weight_kg": 72.5, "fitness_level": "beginner"},
        headers=headers,
    )
    assert response.status_code == 200
    client.patch("/api/v1/profile", json={"display_name": "Renamed"}, headers=headers)
    me = client.get("/api/v1/auth/me", headers=headers).json()
    assert me["goal"] == "weight_loss"
    assert me["weight_kg"] == 72.5
    assert me["display_name"] == "Renamed"


def test_profile_rejects_weight_out_of_range(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    assert client.patch("/api/v1/profile", json={"weight_kg": 5}, headers=headers).status_code == 422
    assert client.patch("/api/v1/profile", json={"weight_kg": 301}, headers=headers).status_code == 422
