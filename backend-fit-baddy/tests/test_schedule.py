"""Module 1 — schedule (US-B2, US-B3; AC2.3–2.4, AC3.2–3.7, AC5.6)."""
from datetime import timedelta

from app.core.clock import utc_now
from tests.conftest import auth_header, create_plan, register_user


def iso(dt):
    return dt.isoformat()


def test_create_slot_is_planned(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    starts = utc_now() + timedelta(days=1)
    response = client.post(
        "/api/v1/schedule",
        json={"title": "Legs", "starts_at": iso(starts), "plan_id": plan["id"]},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "planned"
    assert response.json()["plan_id"] == plan["id"]


def test_slot_in_the_past_is_rejected(client):
    token, _ = register_user(client)
    yesterday = utc_now() - timedelta(days=1)
    response = client.post(
        "/api/v1/schedule", json={"title": "Old", "starts_at": iso(yesterday)}, headers=auth_header(token)
    )
    assert response.status_code == 422


def test_slot_starting_now_is_accepted(client):
    token, _ = register_user(client)
    response = client.post(
        "/api/v1/schedule", json={"title": "Now", "starts_at": iso(utc_now())}, headers=auth_header(token)
    )
    assert response.status_code == 201


def test_slot_with_unknown_plan_is_not_found(client):
    token, _ = register_user(client)
    response = client.post(
        "/api/v1/schedule",
        json={"title": "X", "starts_at": iso(utc_now() + timedelta(hours=2)), "plan_id": 999},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_schedule_is_filtered_by_date_range(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    tomorrow = utc_now() + timedelta(days=1)
    next_week = utc_now() + timedelta(days=7)
    client.post("/api/v1/schedule", json={"title": "Tomorrow", "starts_at": iso(tomorrow)}, headers=headers)
    client.post("/api/v1/schedule", json={"title": "Next week", "starts_at": iso(next_week)}, headers=headers)

    window = {"from": iso(tomorrow - timedelta(hours=1)), "to": iso(tomorrow + timedelta(hours=1))}
    response = client.get("/api/v1/schedule", params=window, headers=headers)
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Tomorrow"]

    assert len(client.get("/api/v1/schedule", headers=headers).json()) == 2


def test_empty_schedule_returns_empty_list(client):
    token, _ = register_user(client)
    response = client.get("/api/v1/schedule", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == []


def test_update_and_delete_slot(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    slot = client.post(
        "/api/v1/schedule", json={"title": "A", "starts_at": iso(utc_now() + timedelta(days=1))}, headers=headers
    ).json()
    moved = utc_now() + timedelta(days=2)
    updated = client.patch(f"/api/v1/schedule/{slot['id']}", json={"starts_at": iso(moved)}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["starts_at"].startswith(moved.date().isoformat())

    assert client.delete(f"/api/v1/schedule/{slot['id']}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/schedule/{slot['id']}", headers=headers).status_code == 404


def test_moving_slot_to_the_past_is_rejected(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    slot = client.post(
        "/api/v1/schedule", json={"title": "A", "starts_at": iso(utc_now() + timedelta(days=1))}, headers=headers
    ).json()
    response = client.patch(
        f"/api/v1/schedule/{slot['id']}", json={"starts_at": iso(utc_now() - timedelta(days=1))}, headers=headers
    )
    assert response.status_code == 422


def test_miss_slot_marks_missed_once(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    slot = client.post(
        "/api/v1/schedule", json={"title": "A", "starts_at": iso(utc_now() + timedelta(hours=1))}, headers=headers
    ).json()
    missed = client.post(f"/api/v1/schedule/{slot['id']}/miss", headers=headers)
    assert missed.status_code == 200
    assert missed.json()["status"] == "missed"
    assert missed.json()["missed_at"]
    assert client.post(f"/api/v1/schedule/{slot['id']}/miss", headers=headers).status_code == 409


def test_cannot_touch_another_users_slot(client):
    owner_token, _ = register_user(client)
    slot = client.post(
        "/api/v1/schedule",
        json={"title": "Mine", "starts_at": iso(utc_now() + timedelta(days=1))},
        headers=auth_header(owner_token),
    ).json()
    other_token, _ = register_user(client, email="other@example.com")
    other = auth_header(other_token)
    assert client.delete(f"/api/v1/schedule/{slot['id']}", headers=other).status_code == 404
    assert client.post(f"/api/v1/schedule/{slot['id']}/miss", headers=other).status_code == 404
