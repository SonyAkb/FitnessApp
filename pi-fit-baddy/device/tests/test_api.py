"""Тесты device/api: контракт docs/pi.md §5 через TestClient в режиме mock."""

import dataclasses
import re
import time
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from device.api.main import create_app
from device.bus.factory import create_bus
from device.clock import ManualClock
from device.config import load_config
from device.services.sampler import Sampler

T0 = datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)
TS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def make(**overrides):
    config = dataclasses.replace(
        load_config(), sensor_mode="mock", scenario="walk", **overrides
    )
    clock = ManualClock()
    bus = create_bus(config)
    sampler = Sampler(
        config, bus, clock, utc_now=lambda: T0 + timedelta(seconds=clock.now())
    )

    def run(seconds):
        for _ in range(round(seconds * config.sample_rate_hz)):
            sampler.tick()
            clock.advance(1.0 / config.sample_rate_hz)

    return sampler, bus, run


def client_for(sampler, **kwargs):
    return TestClient(create_app(sampler=sampler, run_loop=False, **kwargs))


def test_status_contract():
    sampler, _, _ = make()
    with client_for(sampler) as client:
        response = client.get("/device/status")

    assert response.status_code == 200
    assert response.json() == {"connected": True, "battery": 82, "mode": "mock"}


def test_current_after_walk():
    sampler, _, run = make()
    with client_for(sampler) as client:
        first = client.get("/device/vitals/current").json()
        run(20)
        body = client.get("/device/vitals/current").json()

    assert first["heart_rate"] is None
    assert set(body) == {"heart_rate", "steps", "timestamp"}
    assert body["steps"] > 20
    assert abs(body["heart_rate"] - 95) <= 5
    assert TS.match(body["timestamp"])


def test_history_bounds_and_validation():
    sampler, _, run = make()
    with client_for(sampler) as client:
        run(10)
        everything = client.get("/device/vitals/history").json()
        sub = client.get(
            "/device/vitals/history",
            params={"from": "2026-10-14T12:00:03Z", "to": "2026-10-14T12:00:05Z"},
        ).json()
        bad = client.get("/device/vitals/history", params={"from": "вчера"})

    assert len(everything) >= 10
    assert [p["timestamp"] for p in sub] == [
        "2026-10-14T12:00:03Z",
        "2026-10-14T12:00:04Z",
        "2026-10-14T12:00:05Z",
    ]
    assert all(set(p) == {"heart_rate", "steps", "timestamp"} for p in sub)
    assert bad.status_code == 422


def test_dead_sensor_keeps_endpoints_alive():
    sampler, bus, run = make()
    with client_for(sampler) as client:
        run(2)
        devices = dict(bus._devices)  # noqa: SLF001
        bus._devices.clear()  # noqa: SLF001
        run(0.1)

        status = client.get("/device/status")
        current = client.get("/device/vitals/current")
        history = client.get("/device/vitals/history")
        assert status.status_code == current.status_code == history.status_code == 200
        assert status.json()["connected"] is False
        assert current.json()["heart_rate"] is None

        bus._devices.update(devices)  # noqa: SLF001
        run(0.2)
        assert client.get("/device/status").json()["connected"] is True


def test_websocket_sends_immediately_then_periodically():
    sampler, _, _ = make()
    with client_for(sampler, stream_interval_s=0.05) as client:
        with client.websocket_connect("/device/stream") as ws:
            first = ws.receive_json()
            second = ws.receive_json()

    assert set(first) == {"heart_rate", "steps", "timestamp"}
    assert set(second) == set(first)


def test_import_builds_nothing():
    import importlib

    module = importlib.import_module("device.api.main")

    assert not hasattr(module.app.state, "sampler")


def test_handlers_and_loop_share_one_thread():
    import threading

    sampler, _, _ = make(sample_rate_hz=200.0)
    threads = {"tick": set(), "history": set()}
    orig_tick, orig_history = sampler.tick, sampler.history

    def tick():
        threads["tick"].add(threading.get_ident())
        orig_tick()

    def history(*args):
        threads["history"].add(threading.get_ident())
        return orig_history(*args)

    sampler.tick, sampler.history = tick, history
    with TestClient(create_app(sampler=sampler, run_loop=True)) as client:
        for _ in range(5):
            client.get("/device/vitals/history")
            time.sleep(0.01)

    assert len(threads["tick"]) == 1
    assert threads["tick"] == threads["history"]


def test_lifespan_runs_loop_and_shuts_down_cleanly():
    config = dataclasses.replace(
        load_config(), sensor_mode="mock", scenario="walk", sample_rate_hz=200.0
    )
    app = create_app(config)
    with TestClient(app) as client:
        deadline = time.monotonic() + 3.0
        steps = 0
        while time.monotonic() < deadline and steps == 0:
            steps = client.get("/device/vitals/current").json()["steps"]
            time.sleep(0.05)
        assert steps > 0
        assert client.get("/device/status").json()["connected"] is True

    assert app.state.sampler is not None


def test_history_query_edge_cases():
    sampler, _, run = make()
    with client_for(sampler) as client:
        run(10)
        url = "/device/vitals/history"
        offset = client.get(url, params={"from": "2026-10-14T15:00:08+03:00"}).json()
        naive = client.get(url, params={"from": "2026-10-14T12:00:08"}).json()
        to_only = client.get(url, params={"to": "2026-10-14T12:00:01Z"}).json()
        reversed_ = client.get(
            url, params={"from": "2026-10-14T12:00:05Z", "to": "2026-10-14T12:00:02Z"}
        ).json()

    assert offset[0]["timestamp"] == "2026-10-14T12:00:08Z"
    assert naive == offset
    assert [p["timestamp"] for p in to_only] == [
        "2026-10-14T12:00:00Z",
        "2026-10-14T12:00:01Z",
    ]
    assert reversed_ == []
