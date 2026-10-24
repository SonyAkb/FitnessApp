"""Module 2 — plans, sessions, history (US-B1, US-C2, US-C3; AC2.5–2.6, AC3.1, AC4.x, AC5.8, AC8.3–8.6)."""
from tests.conftest import auth_header, complete_workout, create_plan, register_user
import pytest

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
PLANS = "/api/v1/workouts/plans"


def _patch(client, headers, plan_id, body):
    return client.patch(f"{PLANS}/{plan_id}", json=body, headers=headers)


# ---------- PATCH ----------

def test_patch_plan_updates_title_and_description(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)

    response = _patch(client, headers, plan["id"], {"title": "Renamed", "description": "New text"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == body["name"] == "Renamed"
    assert body["description"] == "New text"

    # пустое тело ничего не меняет
    same = _patch(client, headers, plan["id"], {})
    assert same.status_code == 200
    assert same.json()["title"] == "Renamed"


def test_patch_plan_replaces_exercises(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)

    new_exercises = [
        {"name": "Deadlift", "sets": 5, "reps": 5, "weight_kg": 100},
        {"name": "Row", "sets": 3, "reps": 12},
    ]
    response = _patch(client, headers, plan["id"], {"exercises": new_exercises})
    assert response.status_code == 200, response.text
    assert [e["name"] for e in response.json()["exercises"]] == ["Deadlift", "Row"]

    fetched = client.get(f"{PLANS}/{plan['id']}", headers=headers).json()
    assert [e["name"] for e in fetched["exercises"]] == ["Deadlift", "Row"]


@pytest.mark.parametrize(
    "sets,reps",
    [(0, 10), (11, 10), (3, 0), (3, 51)],
)
def test_patch_plan_rejects_out_of_range_sets_and_reps(client, sets, reps):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)

    response = _patch(
        client, headers, plan["id"], {"exercises": [{"name": "Squat", "sets": sets, "reps": reps}]}
    )
    assert response.status_code == 422


@pytest.mark.parametrize("sets,reps", [(1, 1), (10, 50)])
def test_patch_plan_accepts_boundary_values(client, sets, reps):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)

    response = _patch(
        client, headers, plan["id"], {"exercises": [{"name": "Squat", "sets": sets, "reps": reps}]}
    )
    assert response.status_code == 200, response.text


def test_create_plan_rejects_out_of_range_sets(client):
    token, _ = register_user(client)
    response = client.post(
        PLANS,
        json={"title": "Bad", "exercises": [{"name": "Squat", "sets": 11, "reps": 10}]},
        headers=auth_header(token),
    )
    assert response.status_code == 422


def test_patch_unknown_plan_is_not_found(client):
    token, _ = register_user(client)
    assert _patch(client, auth_header(token), 999, {"title": "X"}).status_code == 404


def test_cannot_patch_or_delete_another_users_plan(client):
    token, _ = register_user(client)
    plan = create_plan(client, auth_header(token))
    other_token, _ = register_user(client, email="other@example.com")
    other = auth_header(other_token)

    assert _patch(client, other, plan["id"], {"title": "Hacked"}).status_code == 404
    assert client.delete(f"{PLANS}/{plan['id']}", headers=other).status_code == 404

    still_there = client.get(f"{PLANS}/{plan['id']}", headers=auth_header(token))
    assert still_there.status_code == 200
    assert still_there.json()["title"] == plan["title"]


# ---------- DELETE (архивация) ----------

def test_delete_plan_keeps_history(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    session = complete_workout(client, headers, plan["id"])

    response = client.delete(f"{PLANS}/{plan['id']}", headers=headers)
    assert response.status_code == 204
    assert response.content == b""

    history = client.get("/api/v1/workouts/history", headers=headers).json()
    assert history["total"] == 1
    assert history["items"][0]["id"] == session["id"]
    assert history["items"][0]["plan_name"] == plan["title"]

    # сама сессия тоже открывается
    assert client.get(f"/api/v1/workouts/sessions/{session['id']}", headers=headers).status_code == 200


def test_deleted_plan_is_hidden_everywhere(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    client.delete(f"{PLANS}/{plan['id']}", headers=headers)

    assert client.get(f"{PLANS}/{plan['id']}", headers=headers).status_code == 404
    assert plan["id"] not in [p["id"] for p in client.get(PLANS, headers=headers).json()]
    assert _patch(client, headers, plan["id"], {"title": "X"}).status_code == 404
    assert client.delete(f"{PLANS}/{plan['id']}", headers=headers).status_code == 404
    started = client.post("/api/v1/workouts/sessions", json={"plan_id": plan["id"]}, headers=headers)
    assert started.status_code == 404


def test_plan_write_endpoints_require_auth(client):
    assert client.patch(f"{PLANS}/1", json={"title": "X"}).status_code == 401
    assert client.delete(f"{PLANS}/1").status_code == 401