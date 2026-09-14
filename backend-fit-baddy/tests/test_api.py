from tests.conftest import auth_header, register_user


def test_register_and_login(client):
    token, user = register_user(client)
    assert user["email"] == "demo@example.com"
    assert user["display_name"] == "Demo"
    assert user["role"] == "user"
    assert token

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@example.com", "password": "secret12"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "bearer"
    assert login.json()["user"]["id"] == user["id"]

    me = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "demo@example.com"
    assert "profile" in body
    assert body["profile"]["goal"] is None


def test_unauthorized_access(client):
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401

    pet = client.get("/api/v1/pet")
    assert pet.status_code == 401

    plans = client.get("/api/v1/workouts/plans")
    assert plans.status_code == 401


def test_create_plan_start_and_complete_workout(client):
    token, _ = register_user(client)
    headers = auth_header(token)

    created = client.post(
        "/api/v1/workouts/plans",
        headers=headers,
        json={
            "title": "Legs",
            "exercises": [{"name": "Squat", "sets": 3, "reps": 8, "weight_kg": 60}],
        },
    )
    assert created.status_code == 201, created.text
    plan_id = created.json()["id"]

    fetched = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Legs"
    assert fetched.json()["exercises"][0]["name"] == "Squat"

    started = client.post(
        "/api/v1/workouts/sessions",
        headers=headers,
        json={"workout_plan_id": plan_id},
    )
    assert started.status_code == 201, started.text
    session_id = started.json()["id"]
    assert started.json()["status"] == "in_progress"

    completed = client.post(
        f"/api/v1/workouts/sessions/{session_id}/complete",
        headers=headers,
        json={"duration_seconds": 1200},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["duration_seconds"] == 1200

    history = client.get("/api/v1/workouts/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["id"] == session_id


def test_complete_is_idempotent(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = client.post(
        "/api/v1/workouts/plans",
        headers=headers,
        json={"title": "Push", "exercises": [{"name": "Push-up", "sets": 3, "reps": 10}]},
    ).json()
    session = client.post(
        "/api/v1/workouts/sessions",
        headers=headers,
        json={"workout_plan_id": plan["id"]},
    ).json()

    first = client.post(f"/api/v1/workouts/sessions/{session['id']}/complete", headers=headers, json={})
    assert first.status_code == 200

    second = client.post(f"/api/v1/workouts/sessions/{session['id']}/complete", headers=headers, json={})
    assert second.status_code == 409
    assert "already completed" in second.json()["detail"].lower()


def test_xp_and_level_after_complete(client):
    token, _ = register_user(client)
    headers = auth_header(token)

    pet_before = client.get("/api/v1/pet", headers=headers)
    assert pet_before.status_code == 200
    assert pet_before.json()["xp"] == 0
    assert pet_before.json()["level"] == 1
    assert pet_before.json()["mood"] == "idle"

    plan = client.post(
        "/api/v1/workouts/plans",
        headers=headers,
        json={"title": "Core", "exercises": [{"name": "Plank", "sets": 3, "reps": 30}]},
    ).json()
    session = client.post(
        "/api/v1/workouts/sessions",
        headers=headers,
        json={"workout_plan_id": plan["id"]},
    ).json()
    client.post(
        f"/api/v1/workouts/sessions/{session['id']}/complete",
        headers=headers,
        json={"duration_seconds": 600},
    )

    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["xp"] == 25
    assert pet["level"] == 1
    assert pet["mood"] == "happy"
    assert pet["energy"] > 50
    assert pet["streak_days"] == 1

    dashboard = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard.status_code == 200
    summary = dashboard.json()
    assert summary["completed_workouts_count"] == 1
    assert summary["xp"] == 25
    assert summary["mood"] == "happy"

    notes = client.get("/api/v1/notifications", headers=headers)
    assert notes.status_code == 200
    titles = [n["title"] for n in notes.json()]
    assert "Workout completed" in titles


def test_telemetry_simulate_stores_a_point(client):
    token, _ = register_user(client)
    headers = auth_header(token)

    device = client.post("/api/v1/devices/register", headers=headers, json={"name": "test-watch"})
    assert device.status_code == 201, device.text
    assert device.json()["device_id"]
    assert device.json()["device_token"]

    simulated = client.post("/api/v1/telemetry/simulate", headers=headers)
    assert simulated.status_code == 201, simulated.text
    point = simulated.json()
    assert point["source"] == "simulator"
    assert point["steps"] > 0
    assert point["heart_rate"] > 0
    assert point["calories"] > 0
    assert point["device_id"] == device.json()["device_id"]

    latest = client.get("/api/v1/telemetry/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["steps"] == point["steps"]

    history = client.get("/api/v1/telemetry/history?limit=50", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_mock_webhook_idempotency(client):
    token, user = register_user(client)
    headers = auth_header(token)

    first = client.post(
        "/api/v1/subscription/webhook",
        json={"event_id": "evt_test_1", "type": "checkout.completed", "user_id": user["id"]},
    )
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    assert first.json()["received"] is True
    assert first.json()["plan"] == "pro"

    second = client.post(
        "/api/v1/subscription/webhook",
        json={"event_id": "evt_test_1", "type": "checkout.completed", "user_id": user["id"]},
    )
    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    sub = client.get("/api/v1/subscription", headers=headers)
    assert sub.status_code == 200
    assert sub.json()["plan"] == "pro"
    assert sub.json()["status"] == "active"


def test_full_demo_path(client):
    token, _ = register_user(client, email="path@example.com")
    headers = auth_header(token)

    client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"goal": "muscle_gain", "weight_kg": 80, "fitness_level": "beginner"},
    )
    plan = client.post(
        "/api/v1/workouts/plans",
        headers=headers,
        json={"title": "Demo", "exercises": [{"name": "Squat", "sets": 3, "reps": 8, "weight_kg": 40}]},
    ).json()
    session = client.post(
        "/api/v1/workouts/sessions",
        headers=headers,
        json={"workout_plan_id": plan["id"]},
    ).json()
    complete = client.post(
        f"/api/v1/workouts/sessions/{session['id']}/complete",
        headers=headers,
        json={"duration_seconds": 900},
    )
    assert complete.status_code == 200

    pet = client.get("/api/v1/pet", headers=headers).json()
    assert pet["xp"] == 25
    assert pet["mood"] == "happy"

    dashboard = client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert dashboard["completed_workouts_count"] == 1
    assert dashboard["xp"] == 25

    notes = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notes) >= 1

    sim = client.post("/api/v1/telemetry/simulate", headers=headers)
    assert sim.status_code == 201
    latest = client.get("/api/v1/telemetry/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["heart_rate"] == sim.json()["heart_rate"]
