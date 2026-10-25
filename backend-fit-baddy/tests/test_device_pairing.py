"""Module 5 — pairing a Raspberry Pi by code, ingest from the device, Health Connect batch (DEV-05, DEV-06)."""
from datetime import timedelta

from app.core.clock import utc_now
from app.modules.devices import service
from tests.conftest import auth_header, register_user


def pair_pi(client, token: str, device_id: str = "pi-livingroom-01") -> dict:
    code = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()["code"]
    response = client.post("/api/v1/devices/pair", json={"code": code, "device_id": device_id})
    assert response.status_code == 200, response.text
    return response.json()


def point(device_id: str = "pi-livingroom-01", **overrides) -> dict:
    body = {"device_id": device_id, "steps": 120, "heart_rate": 74, "calories": 5,
            "timestamp": "2026-10-25T10:00:00Z", "source": "raspberry_pi"}
    body.update(overrides)
    return body


def test_pairing_code_requires_user(client):
    assert client.post("/api/v1/devices/pairing").status_code == 401


def test_pairing_code_is_six_digits_and_expires(client):
    token, _ = register_user(client)
    body = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()
    assert len(body["code"]) == 6 and body["code"].isdigit()
    assert body["kind"] == "raspberry_pi"
    assert body["expires_at"]


def test_pair_issues_token_and_device_appears_in_list(client):
    token, user = register_user(client)
    device = pair_pi(client, token)
    assert device["user_id"] == user["id"]
    assert device["kind"] == "raspberry_pi"
    assert device["device_token"]
    listed = client.get("/api/v1/devices", headers=auth_header(token)).json()
    assert [(d["device_id"], d["kind"], d["last_seen_at"]) for d in listed] == [("pi-livingroom-01", "raspberry_pi", None)]
    assert "device_token" not in listed[0]


def test_pairing_code_is_single_use(client):
    token, _ = register_user(client)
    code = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()["code"]
    assert client.post("/api/v1/devices/pair", json={"code": code, "device_id": "pi-1"}).status_code == 200
    assert client.post("/api/v1/devices/pair", json={"code": code, "device_id": "pi-1"}).status_code == 404


def test_unknown_or_malformed_code_is_rejected(client):
    assert client.post("/api/v1/devices/pair", json={"code": "000000", "device_id": "pi-1"}).status_code == 404
    assert client.post("/api/v1/devices/pair", json={"code": "12ab", "device_id": "pi-1"}).status_code == 422


def test_expired_code_is_rejected(client):
    token, user = register_user(client)
    code = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()["code"]
    service._pairings[code].expires_at = utc_now() - timedelta(seconds=1)
    assert client.post("/api/v1/devices/pair", json={"code": code, "device_id": "pi-1"}).status_code == 404


def test_new_code_replaces_previous_one(client):
    token, _ = register_user(client)
    first = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()["code"]
    second = client.post("/api/v1/devices/pairing", headers=auth_header(token)).json()["code"]
    assert first not in service._pairings and second in service._pairings


def test_pairing_device_of_another_user_conflicts(client):
    alice, _ = register_user(client, "alice@example.com")
    bob, _ = register_user(client, "bob@example.com")
    pair_pi(client, alice, "pi-shared")
    code = client.post("/api/v1/devices/pairing", headers=auth_header(bob)).json()["code"]
    response = client.post("/api/v1/devices/pair", json={"code": code, "device_id": "pi-shared"})
    assert response.status_code == 409
    assert "device_token" not in response.text


def test_repairing_rotates_token(client):
    token, _ = register_user(client)
    old = pair_pi(client, token)["device_token"]
    new = pair_pi(client, token)["device_token"]
    assert old != new
    assert client.post("/api/v1/telemetry/ingest", json=point(), headers={"X-Device-Token": old}).status_code == 401
    assert client.post("/api/v1/telemetry/ingest", json=point(), headers={"X-Device-Token": new}).status_code == 201


def test_ingest_requires_valid_device_token(client):
    assert client.post("/api/v1/telemetry/ingest", json=point()).status_code == 401
    assert client.post("/api/v1/telemetry/ingest", json=point(), headers={"X-Device-Token": "nope"}).status_code == 401


def test_ingest_rejects_token_of_another_device(client):
    token, _ = register_user(client)
    device_token = pair_pi(client, token)["device_token"]
    response = client.post("/api/v1/telemetry/ingest", json=point("pi-other"), headers={"X-Device-Token": device_token})
    assert response.status_code == 403


def test_ingest_validates_values(client):
    token, _ = register_user(client)
    headers = {"X-Device-Token": pair_pi(client, token)["device_token"]}
    for bad in ({"heart_rate": 20}, {"heart_rate": 260}, {"steps": -1}, {"calories": -3}):
        assert client.post("/api/v1/telemetry/ingest", json=point(**bad), headers=headers).status_code == 422


def test_ingested_point_is_visible_to_the_user(client):
    token, user = register_user(client)
    headers = {"X-Device-Token": pair_pi(client, token)["device_token"]}
    response = client.post("/api/v1/telemetry/ingest", json=point(), headers=headers)
    assert response.status_code == 201
    assert response.json()["source"] == "raspberry_pi"
    assert response.json()["user_id"] == user["id"]
    latest = client.get("/api/v1/telemetry/latest", headers=auth_header(token)).json()
    assert (latest["device_id"], latest["steps"], latest["heart_rate"]) == ("pi-livingroom-01", 120, 74)
    listed = client.get("/api/v1/devices", headers=auth_header(token)).json()
    assert listed[0]["last_seen_at"] is not None


def test_repeated_point_is_stored_once(client):
    token, _ = register_user(client)
    headers = {"X-Device-Token": pair_pi(client, token)["device_token"]}
    assert client.post("/api/v1/telemetry/ingest", json=point(), headers=headers).status_code == 201
    assert client.post("/api/v1/telemetry/ingest", json=point(), headers=headers).status_code == 200
    assert len(client.get("/api/v1/telemetry/history", headers=auth_header(token)).json()) == 1


def test_unlinked_device_can_no_longer_send(client):
    token, _ = register_user(client)
    headers = {"X-Device-Token": pair_pi(client, token)["device_token"]}
    client.post("/api/v1/telemetry/ingest", json=point(), headers=headers)
    assert client.delete("/api/v1/devices/pi-livingroom-01", headers=auth_header(token)).status_code == 204
    assert client.post("/api/v1/telemetry/ingest", json=point(timestamp="2026-10-25T10:00:05Z"), headers=headers).status_code == 401
    assert client.get("/api/v1/devices", headers=auth_header(token)).json() == []
    assert len(client.get("/api/v1/telemetry/history", headers=auth_header(token)).json()) == 1  # history stays


def test_cannot_unlink_device_of_another_user(client):
    alice, _ = register_user(client, "alice@example.com")
    bob, _ = register_user(client, "bob@example.com")
    pair_pi(client, alice)
    assert client.delete("/api/v1/devices/pi-livingroom-01", headers=auth_header(bob)).status_code == 404


def test_simulator_keeps_its_own_device_after_pairing(client):
    token, _ = register_user(client)
    pair_pi(client, token)
    simulated = client.post("/api/v1/telemetry/simulate", headers=auth_header(token)).json()
    assert simulated["source"] == "simulator"
    assert simulated["device_id"] != "pi-livingroom-01"


def test_health_connect_batch_skips_duplicates(client):
    token, _ = register_user(client)
    points = [
        {"steps": 3000, "heart_rate": 70, "calories": 120, "timestamp": "2026-10-25T09:00:00Z"},
        {"steps": 3500, "heart_rate": 88, "calories": 140, "timestamp": "2026-10-25T09:15:00Z"},
    ]
    first = client.post("/api/v1/telemetry/batch", json={"points": points}, headers=auth_header(token)).json()
    assert (first["accepted"], first["duplicates"]) == (2, 0)
    again = client.post("/api/v1/telemetry/batch", json={"points": points}, headers=auth_header(token)).json()
    assert (again["accepted"], again["duplicates"]) == (0, 2)
    latest = client.get("/api/v1/telemetry/latest", headers=auth_header(token)).json()
    assert (latest["source"], latest["steps"]) == ("health_connect", 3500)
    kinds = [d["kind"] for d in client.get("/api/v1/devices", headers=auth_header(token)).json()]
    assert kinds == ["health_connect"]


def test_health_connect_batch_requires_user_and_valid_points(client):
    assert client.post("/api/v1/telemetry/batch", json={"points": []}).status_code == 401
    token, _ = register_user(client)
    bad = {"points": [{"steps": 1, "heart_rate": 300, "timestamp": "2026-10-25T09:00:00Z"}]}
    assert client.post("/api/v1/telemetry/batch", json=bad, headers=auth_header(token)).status_code == 422
    assert client.post("/api/v1/telemetry/batch", json={"points": []}, headers=auth_header(token)).status_code == 422


def test_websocket_streams_points_from_the_pi_without_simulating(client):
    token, _ = register_user(client)
    headers = {"X-Device-Token": pair_pi(client, token)["device_token"]}
    client.post("/api/v1/telemetry/ingest", json=point(), headers=headers)
    with client.websocket_connect(f"/api/v1/telemetry/ws?token={token}") as ws:
        first = ws.receive_json()
        client.post("/api/v1/telemetry/ingest", json=point(steps=150, timestamp="2026-10-25T10:00:05Z"), headers=headers)
        second = ws.receive_json()
    assert (first["source"], first["steps"]) == ("raspberry_pi", 120)
    assert (second["source"], second["steps"]) == ("raspberry_pi", 150)
    history = client.get("/api/v1/telemetry/history", headers=auth_header(token)).json()
    assert {p["source"] for p in history} == {"raspberry_pi"}
