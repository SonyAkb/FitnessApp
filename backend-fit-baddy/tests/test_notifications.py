"""Module 4 — notifications and dashboard (US-E1, US-F2; AC8.1–8.2, AC9.x)."""
from datetime import timedelta

from app.core.clock import utc_now
from tests.conftest import auth_header, complete_workout, register_user


def test_empty_notification_center(client):
    token, _ = register_user(client)
    response = client.get("/api/v1/notifications", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == []


def test_completed_and_missed_workouts_create_notifications(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)
    slot = client.post(
        "/api/v1/schedule", json={"title": "A", "starts_at": (utc_now() + timedelta(hours=1)).isoformat()},
        headers=headers,
    ).json()
    client.post(f"/api/v1/schedule/{slot['id']}/miss", headers=headers)

    kinds = [note["kind"] for note in client.get("/api/v1/notifications", headers=headers).json()]
    assert kinds[0] == "workout_missed", "newest first"
    assert "workout_completed" in kinds


def test_mark_read_and_unread_filter(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)
    complete_workout(client, headers)
    notes = client.get("/api/v1/notifications", headers=headers).json()
    read = client.post(f"/api/v1/notifications/{notes[0]['id']}/read", headers=headers)
    assert read.status_code == 200
    assert read.json()["is_read"] is True

    unread = client.get("/api/v1/notifications", params={"unread_only": True}, headers=headers).json()
    assert all(note["is_read"] is False for note in unread)
    assert len(unread) == len(notes) - 1


def test_notification_limit(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    for _ in range(3):
        complete_workout(client, headers)
    assert len(client.get("/api/v1/notifications", params={"limit": 2}, headers=headers).json()) == 2


def test_cannot_read_another_users_notification(client):
    token, _ = register_user(client)
    complete_workout(client, auth_header(token))
    note_id = client.get("/api/v1/notifications", headers=auth_header(token)).json()[0]["id"]
    other_token, _ = register_user(client, email="other@example.com")
    assert client.post(f"/api/v1/notifications/{note_id}/read", headers=auth_header(other_token)).status_code == 404


def test_dashboard_summary_fields(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    complete_workout(client, headers)
    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    for field in (
        "total_workouts", "completed_workouts", "missed_workouts", "current_streak_days",
        "xp", "level", "companion_mood", "steps_7d", "period",
    ):
        assert field in body
    assert body["completed_workouts"] == 1
    assert body["missed_workouts"] == 0
