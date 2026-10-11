"""Module 2 — plans, sessions, history (US-B1, US-C2, US-C3; AC2.5–2.6, AC3.1, AC4.x, AC5.8, AC8.3–8.6)."""
from tests.conftest import auth_header, complete_workout, create_plan, register_user


def test_plan_without_exercises_has_empty_list(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = client.post("/api/v1/workouts/plans", json={"name": "Empty"}, headers=headers).json()
    fetched = client.get(f"/api/v1/workouts/plans/{plan['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["exercises"] == []


def test_plan_requires_title(client):
    token, _ = register_user(client)
    response = client.post("/api/v1/workouts/plans", json={"exercises": []}, headers=auth_header(token))
    assert response.status_code == 422


def test_session_requires_plan_id(client):
    token, _ = register_user(client)
    response = client.post("/api/v1/workouts/sessions", json={}, headers=auth_header(token))
    assert response.status_code == 422


def test_session_for_unknown_plan_is_not_found(client):
    token, _ = register_user(client)
    response = client.post("/api/v1/workouts/sessions", json={"plan_id": 999}, headers=auth_header(token))
    assert response.status_code == 404


def test_second_session_for_same_plan_is_allowed(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    first = client.post("/api/v1/workouts/sessions", json={"plan_id": plan["id"]}, headers=headers)
    second = client.post("/api/v1/workouts/sessions", json={"plan_id": plan["id"]}, headers=headers)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_complete_with_explicit_duration(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    session = client.post("/api/v1/workouts/sessions", json={"plan_id": plan["id"]}, headers=headers).json()
    done = client.post(
        f"/api/v1/workouts/sessions/{session['id']}/complete", json={"duration_seconds": 2400}, headers=headers
    )
    assert done.status_code == 200
    assert done.json()["duration_seconds"] == 2400
    assert done.json()["xp_awarded"] > 0


def test_cannot_complete_another_users_session(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    session = client.post("/api/v1/workouts/sessions", json={"plan_id": plan["id"]}, headers=headers).json()
    other_token, _ = register_user(client, email="other@example.com")
    response = client.post(
        f"/api/v1/workouts/sessions/{session['id']}/complete", json={}, headers=auth_header(other_token)
    )
    assert response.status_code == 404


def test_history_is_paginated_newest_first(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    ids = [complete_workout(client, headers, plan["id"])["id"] for _ in range(3)]

    page = client.get("/api/v1/workouts/history", params={"limit": 2, "offset": 0}, headers=headers).json()
    assert page["total"] == 3
    assert [item["id"] for item in page["items"]] == [ids[2], ids[1]]

    rest = client.get("/api/v1/workouts/history", params={"limit": 2, "offset": 2}, headers=headers).json()
    assert [item["id"] for item in rest["items"]] == [ids[0]]

    beyond = client.get("/api/v1/workouts/history", params={"offset": 10}, headers=headers)
    assert beyond.status_code == 200
    assert beyond.json()["items"] == []


def test_history_defaults_to_20_items(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    for _ in range(21):
        complete_workout(client, headers, plan["id"])
    body = client.get("/api/v1/workouts/history", headers=headers).json()
    assert len(body["items"]) == 20
    assert body["total"] == 21
