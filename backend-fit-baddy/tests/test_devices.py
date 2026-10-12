"""Module 5 — devices and telemetry (US-H1; AC7.x, AC8.5, AC12.3–12.4, AC-G5) and the TelemetryDTO contract."""
from datetime import timedelta

from app.core.clock import utc_now
from app.modules.devices import schemas
from tests.conftest import auth_header, register_user

# Fields of TelemetryDTO from docs/API_CONTRACT.md — shared by the simulator and Raspberry Pi.
TELEMETRY_DTO_FIELDS = {"device_id", "user_id", "steps", "heart_rate", "calories", "timestamp", "source"}


def test_telemetry_out_matches_contract():
    assert set(schemas.TelemetryOut.model_fields) == TELEMETRY_DTO_FIELDS


def test_simulator_and_pi_points_have_identical_shape(client, db_session):
    from app.modules.devices import service

    _, user = register_user(client)
    sim = service.store_sample(
        db_session, user["id"], "sim-1",
        {"steps": 100, "heart_rate": 80, "calories": 4, "timestamp": utc_now(), "source": "simulator"},
    )
    pi = service.store_sample(
        db_session, user["id"], "pi-1",
        {"steps": 120, "heart_rate": 75, "calories": 5, "timestamp": utc_now(), "source": "raspberry_pi"},
    )
    sim_out = schemas.TelemetryOut.model_validate(sim).model_dump()
    pi_out = schemas.TelemetryOut.model_validate(pi).model_dump()
    assert set(sim_out) == set(pi_out) == TELEMETRY_DTO_FIELDS
    assert (sim_out["source"], pi_out["source"]) == ("simulator", "raspberry_pi")


def test_latest_without_points_is_not_found(client):
    token, _ = register_user(client)
    assert client.get("/api/v1/telemetry/latest", headers=auth_header(token)).status_code == 404


def test_simulate_rejects_negative_values(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    for body in ({"steps": -1}, {"heart_rate": -5}, {"calories": -10}):
        assert client.post("/api/v1/telemetry/simulate", json=body, headers=headers).status_code == 422


def test_simulate_without_registration_creates_device(client):
    token, _ = register_user(client)
    point = client.post("/api/v1/telemetry/simulate", headers=auth_header(token))
    assert point.status_code == 201
    assert point.json()["source"] == "simulator"
    assert point.json()["device_id"]


def test_register_same_device_twice_is_idempotent(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    first = client.post("/api/v1/devices/register", json={"device_id": "watch-1"}, headers=headers)
    second = client.post("/api/v1/devices/register", json={"device_id": "watch-1"}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["device_token"] == first.json()["device_token"]


def test_device_of_another_user_conflicts_without_leaking_token(client):
    owner, _ = register_user(client)
    client.post("/api/v1/devices/register", json={"device_id": "watch-1"}, headers=auth_header(owner))
    other, _ = register_user(client, email="other@example.com")
    response = client.post("/api/v1/devices/register", json={"device_id": "watch-1"}, headers=auth_header(other))
    assert response.status_code == 409
    assert "device_token" not in response.text


def test_history_is_filtered_by_period(client):
    token, _ = register_user(client)
    headers = auth_header(token)
    client.post("/api/v1/telemetry/simulate", headers=headers)
    future = {"from": (utc_now() + timedelta(days=1)).isoformat()}
    assert client.get("/api/v1/telemetry/history", params=future, headers=headers).json() == []
    past = {"from": (utc_now() - timedelta(days=1)).isoformat(), "to": (utc_now() + timedelta(minutes=1)).isoformat()}
    points = client.get("/api/v1/telemetry/history", params=past, headers=headers).json()
    assert len(points) == 1
    assert points[0]["source"] == "simulator"


def test_websocket_rejects_invalid_token(client):
    with client.websocket_connect("/api/v1/telemetry/ws?token=bad") as ws:
        message = ws.receive()
    assert message["type"] == "websocket.close"
    assert message["code"] == 4401


def test_websocket_streams_telemetry_dto(client):
    token, _ = register_user(client)
    with client.websocket_connect(f"/api/v1/telemetry/ws?token={token}") as ws:
        point = ws.receive_json()
    assert set(point) == TELEMETRY_DTO_FIELDS
