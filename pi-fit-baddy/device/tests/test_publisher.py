"""Тесты Publisher (PI-09) на подменённом HTTP-клиенте httpx.MockTransport."""

import asyncio
import dataclasses
import functools
import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from device.api.main import create_app
from device.bus.factory import create_bus
from device.clock import ManualClock
from device.config import load_config
from device.services.publisher import BUFFER_MAX_POINTS, Publisher
from device.services.sampler import Reading, Sampler

T0 = datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)
TOKEN = "super-secret-token-xyz"
URL = "http://backend:8000"


def sync(fn):
    """pytest-asyncio нет в зависимостях: гоняем корутину через asyncio.run."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))

    return wrapper


def ts(n: int) -> str:
    return (T0 + timedelta(seconds=n)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeSampler:
    """Минимальная замена Sampler: каждое показание на секунду позже."""

    def __init__(self, heart_rate=95, steps=28):
        self.heart_rate = heart_rate
        self.steps = steps
        self.n = 0

    def current(self):
        self.n += 1
        return Reading(self.heart_rate, self.steps, T0 + timedelta(seconds=self.n))


class Backend:
    def __init__(self, *responses):
        self.requests: list[httpx.Request] = []
        self.script = list(responses)  # int | Exception; когда кончились -> 201

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.script.pop(0) if self.script else 201
        if isinstance(item, Exception):
            raise item
        return httpx.Response(item, json={"detail": "x"})

    def bodies(self):
        return [json.loads(r.content) for r in self.requests]


def make(backend, sampler=None, **kw):
    client = httpx.AsyncClient(transport=httpx.MockTransport(backend.handler))
    params = dict(
        backend_url=URL,
        device_id="pi-01",
        device_token=TOKEN,
        interval_s=5,
        calories_per_step=0.04,
    )
    params.update(kw)
    return Publisher(sampler or FakeSampler(), client, **params)


@sync
async def test_request_format():
    backend = Backend()
    pub = make(backend)
    await pub.publish_once()

    (req,) = backend.requests
    assert req.method == "POST"
    assert str(req.url) == "http://backend:8000/api/v1/telemetry/ingest"
    assert req.headers["X-Device-Token"] == TOKEN
    assert json.loads(req.content) == {
        "device_id": "pi-01",
        "steps": 28,
        "heart_rate": 95,
        "calories": 1,
        "timestamp": "2026-10-14T12:00:01Z",
        "source": "raspberry_pi",
    }
    assert pub.pending == 0


@pytest.mark.parametrize("url", ["http://h:8000", "http://h:8000/"])
@sync
async def test_url_normalized(url):
    backend = Backend()
    await make(backend, backend_url=url).publish_once()
    assert str(backend.requests[0].url) == "http://h:8000/api/v1/telemetry/ingest"


@pytest.mark.parametrize("hr", [None, 29, 231, 0])
@sync
async def test_no_valid_heart_rate_skipped(hr):
    backend = Backend()
    pub = make(backend, FakeSampler(heart_rate=hr))
    await pub.publish_once()
    assert backend.requests == []
    assert pub.pending == 0


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ConnectError("нет связи"),
        httpx.ReadTimeout("таймаут"),
        httpx.DecodingError("битый ответ"),
        503,
        500,
        408,
        429,
    ],
)
@sync
async def test_transient_failure_keeps_point(failure):
    backend = Backend(failure)
    pub = make(backend)
    await pub.publish_once()
    assert pub.pending == 1
    await pub.publish_once()  # backend вернулся
    assert pub.pending == 0
    assert [b["timestamp"] for b in backend.bodies()] == [ts(1), ts(1), ts(2)]


@sync
async def test_order_preserved_after_outage():
    backend = Backend(503, 503, 503)
    pub = make(backend)
    for _ in range(3):
        await pub.publish_once()
    assert pub.pending == 3
    backend.requests.clear()
    await pub.publish_once()
    assert [b["timestamp"] for b in backend.bodies()] == [ts(i) for i in (1, 2, 3, 4)]
    assert pub.pending == 0


@sync
async def test_failure_stops_cycle():
    backend = Backend(503, 201, 503)
    pub = make(backend)
    await pub.publish_once()  # p1 -> 503
    await pub.publish_once()  # p1 -> 201, p2 -> 503, цикл прерван
    assert pub.pending == 1
    assert backend.bodies()[-1]["timestamp"] == ts(2)


@sync
async def test_buffer_bounded_drops_oldest():
    extra = 20
    backend = Backend(*[503] * (BUFFER_MAX_POINTS + extra))
    pub = make(backend)
    for _ in range(BUFFER_MAX_POINTS + extra):
        await pub.publish_once()
    assert pub.pending == BUFFER_MAX_POINTS
    backend.requests.clear()
    await pub.publish_once()  # ещё одна точка вытесняет старейшую
    bodies = backend.bodies()
    assert len(bodies) == BUFFER_MAX_POINTS
    assert bodies[0]["timestamp"] == ts(extra + 2)
    assert bodies[-1]["timestamp"] == ts(BUFFER_MAX_POINTS + extra + 1)


@pytest.mark.parametrize("code", [401, 403, 422, 400])
@sync
async def test_permanent_rejection_dropped(code, caplog):
    backend = Backend(code)
    pub = make(backend)
    with caplog.at_level(logging.DEBUG):
        await pub.publish_once()
        await pub.publish_once()
    assert pub.pending == 0
    assert [b["timestamp"] for b in backend.bodies()] == [ts(1), ts(2)]  # без повтора
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert errors
    if code in (401, 403):
        assert "DEVICE_TOKEN" in errors[0].getMessage()
    assert TOKEN not in caplog.text


@sync
async def test_token_not_in_repr_or_logs(caplog):
    backend = Backend(httpx.ConnectError("x"), 401)
    pub = make(backend)
    with caplog.at_level(logging.DEBUG):
        await pub.publish_once()
        await pub.publish_once()
    assert TOKEN not in repr(pub)
    assert TOKEN not in caplog.text


@pytest.mark.parametrize("code", [200, 202, 204])
@sync
async def test_any_2xx_is_success(code, caplog):
    backend = Backend(code)
    pub = make(backend)
    with caplog.at_level(logging.DEBUG):
        await pub.publish_once()
    assert pub.pending == 0
    assert "отклонил" not in caplog.text


@pytest.mark.parametrize("code", [301, 307])
@sync
async def test_redirect_dropped_with_url_hint(code, caplog):
    backend = Backend(code)
    pub = make(backend)
    with caplog.at_level(logging.DEBUG):
        await pub.publish_once()
    assert pub.pending == 0
    assert "BACKEND_URL" in caplog.text and "https" in caplog.text
    assert "отклонил" not in caplog.text


@sync
async def test_buffer_eviction_warns(caplog):
    backend = Backend(*[503] * (BUFFER_MAX_POINTS + 1))
    pub = make(backend)
    with caplog.at_level(logging.WARNING):
        for _ in range(BUFFER_MAX_POINTS):
            await pub.publish_once()
        assert "вытеснена" not in caplog.text
        await pub.publish_once()
    assert "вытеснена" in caplog.text


@sync
async def test_skipped_points_lose_no_steps():
    sampler = FakeSampler(heart_rate=None, steps=10)
    backend = Backend()
    pub = make(backend, sampler)
    await pub.publish_once()
    sampler.steps = 55
    await pub.publish_once()
    assert backend.requests == []
    sampler.heart_rate = 90
    sampler.steps = 80
    await pub.publish_once()
    assert [b["steps"] for b in backend.bodies()] == [80]


@pytest.mark.parametrize(
    "kw",
    [
        {"backend_url": "backend:8000"},
        {"backend_url": "ftp://backend"},
        {"backend_url": "http://"},
        {"device_id": "   "},
        {"device_token": "abc\ndef"},
        {"device_token": "ab\x00c"},
    ],
)
def test_invalid_settings_raise_without_token(kw):
    with pytest.raises(ValueError) as exc:
        make(Backend(), **kw)
    assert "abc" not in str(exc.value) and TOKEN not in str(exc.value)


@pytest.mark.parametrize("missing", ["backend_url", "device_id", "device_token"])
def test_missing_settings_raise(missing):
    with pytest.raises(ValueError) as exc:
        make(Backend(), **{missing: ""})
    assert TOKEN not in str(exc.value)


def test_interval_validated():
    with pytest.raises(ValueError):
        make(Backend(), interval_s=0)


@sync
async def test_run_schedule_no_drift():
    clock = ManualClock()
    backend = Backend()
    pub = make(backend, clock=clock, interval_s=5)
    delays = []

    async def fake_sleep(delay):
        delays.append(delay)
        clock.advance(delay + 0.3)  # публикация «съедает» время
        if len(delays) == 4:
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await pub.run(sleep=fake_sleep)

    assert delays[0] == 5  # первая отправка через один интервал
    assert delays[1:] == pytest.approx([4.7, 4.7, 4.7])
    assert len(backend.requests) == 3


@sync
async def test_run_survives_unexpected_error(caplog):
    clock = ManualClock()
    sampler = FakeSampler()
    original = sampler.current
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return original()

    sampler.current = flaky
    backend = Backend()
    pub = make(backend, sampler, clock=clock)
    cycles = 0

    async def fake_sleep(delay):
        nonlocal cycles
        cycles += 1
        clock.advance(delay)
        if cycles == 4:
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await pub.run(sleep=fake_sleep)
    assert len(backend.requests) == 2
    assert "RuntimeError" in caplog.text


# --- lifespan и полный путь -----------------------------------------------


def _config(**overrides):
    return dataclasses.replace(
        load_config(), sensor_mode="mock", scenario="walk", **overrides
    )


def _sampler(config):
    clock = ManualClock()
    sampler = Sampler(
        config,
        create_bus(config),
        clock,
        utc_now=lambda: T0 + timedelta(seconds=clock.now()),
    )
    return sampler, clock


def test_disabled_by_default_no_publisher():
    config = _config(publish_enabled=False)
    sampler, _ = _sampler(config)
    with TestClient(create_app(config, sampler=sampler)) as client:
        assert client.app.state.publisher is None


def test_enabled_without_settings_fails_startup():
    config = _config(
        publish_enabled=True, backend_url=None, device_id=None, device_token=None
    )
    sampler, _ = _sampler(config)
    with pytest.raises(ValueError, match="BACKEND_URL"):
        with TestClient(create_app(config, sampler=sampler)):
            pass


def test_lifespan_starts_and_stops_publisher():
    config = _config(
        publish_enabled=True, backend_url=URL, device_id="pi-01", device_token=TOKEN
    )
    sampler, _ = _sampler(config)
    with TestClient(create_app(config, sampler=sampler)) as client:
        pub = client.app.state.publisher
        assert isinstance(pub, Publisher)
        assert TOKEN not in repr(pub)
        http_client = pub._client
        assert not http_client.is_closed
    assert http_client.is_closed


def test_lifespan_runs_and_cancels_injected_publisher():
    events = []

    class Stub:
        async def run(self):
            events.append("started")
            try:
                await asyncio.sleep(3600)
            finally:
                events.append("cancelled")

    config = _config()
    sampler, _ = _sampler(config)
    with TestClient(create_app(config, sampler=sampler, publisher=Stub())):
        pass
    assert events == ["started", "cancelled"]


@sync
async def test_full_path_sampler_to_publisher():
    config = _config()
    sampler, clock = _sampler(config)
    backend = Backend()
    pub = make(backend, sampler)
    for _ in range(round(20 * config.sample_rate_hz)):
        sampler.tick()
        clock.advance(1.0 / config.sample_rate_hz)
    await pub.publish_once()

    (body,) = backend.bodies()
    assert set(body) == {
        "device_id",
        "steps",
        "heart_rate",
        "calories",
        "timestamp",
        "source",
    }
    assert body["steps"] > 20
    assert abs(body["heart_rate"] - 95) <= 5
    assert body["calories"] == round(body["steps"] * 0.04)
