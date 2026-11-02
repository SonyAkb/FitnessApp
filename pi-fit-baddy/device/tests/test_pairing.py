"""Сопряжение узла по коду из приложения: обмен кода на токен и его сохранение."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import stat

import httpx
import pytest
from fastapi.testclient import TestClient

from device.api.main import create_app
from device.config import load_config
from device.services import pairing
from device.services.pairing import Credentials, PairingError, resolve_credentials
from device.services.publisher import Publisher

URL = "http://backend.test:8000"


def _config(tmp_path, **overrides):
    base = dict(sensor_mode="mock", scenario="walk", backend_url=URL, device_id=None, device_token=None,
                pairing_code=None, device_token_file=str(tmp_path / "token.json"))
    base.update(overrides)
    return dataclasses.replace(load_config(), **base)


def _client(status=200, body=None, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append((str(request.url), json.loads(request.content)))
        return httpx.Response(status, json=body if body is not None else {})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _resolve(config, client):
    async def go():
        async with client:
            return await resolve_credentials(config, client)
    return asyncio.run(go())


def test_code_is_exchanged_for_token_and_saved(tmp_path):
    calls = []
    config = _config(tmp_path, pairing_code="123456", device_id="pi-01")
    creds = _resolve(config, _client(body={"device_token": "tok-1", "device_id": "pi-01"}, calls=calls))
    assert creds == Credentials(device_id="pi-01", device_token="tok-1")
    assert calls == [(URL + "/api/v1/devices/pair", {"code": "123456", "device_id": "pi-01"})]
    saved = json.loads((tmp_path / "token.json").read_text())
    assert saved == {"backend_url": URL, "device_id": "pi-01", "device_token": "tok-1"}
    assert stat.S_IMODE(os.stat(tmp_path / "token.json").st_mode) == 0o600


def test_device_id_defaults_to_hostname(tmp_path, monkeypatch):
    monkeypatch.setattr(pairing.socket, "gethostname", lambda: "RaspberryPi 4.local")
    calls = []
    _resolve(_config(tmp_path, pairing_code="123456"), _client(body={"device_token": "t"}, calls=calls))
    assert calls[0][1]["device_id"] == "pi-raspberrypi-4-local"


def test_saved_token_is_used_without_code(tmp_path):
    pairing.save(str(tmp_path / "token.json"), backend_url=URL, credentials=Credentials("pi-01", "tok-1"))
    creds = _resolve(_config(tmp_path), _client(status=500))
    assert creds == Credentials("pi-01", "tok-1")


def test_saved_token_for_another_backend_is_ignored(tmp_path):
    pairing.save(str(tmp_path / "token.json"), backend_url="http://old:8000", credentials=Credentials("pi-01", "tok-1"))
    assert _resolve(_config(tmp_path), _client(status=500)) is None


def test_explicit_device_token_wins(tmp_path):
    calls = []
    config = _config(tmp_path, device_token="env-token", device_id="pi-01", pairing_code="123456")
    assert _resolve(config, _client(calls=calls)) is None
    assert calls == []


@pytest.mark.parametrize(
    ("status", "message"),
    [(404, "истёк"), (409, "другому пользователю"), (422, "6 цифр"), (500, "500")],
)
def test_pairing_errors_are_explained(tmp_path, status, message):
    with pytest.raises(PairingError, match=message):
        _resolve(_config(tmp_path, pairing_code="123456", device_id="pi-01"), _client(status=status))
    assert not (tmp_path / "token.json").exists()


def test_backend_unreachable(tmp_path):
    def handler(request):
        raise httpx.ConnectError("refused")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(PairingError, match="BACKEND_URL"):
        _resolve(_config(tmp_path, pairing_code="123456", device_id="pi-01"), client)


def test_emulator_address_gets_a_hint(tmp_path):
    def handler(request):
        raise httpx.ConnectTimeout("timeout")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = _config(tmp_path, backend_url="http://10.0.2.2:8000", pairing_code="123456", device_id="pi-01")
    with pytest.raises(PairingError, match="localhost:8000"):
        _resolve(config, client)


def test_startup_publishes_with_saved_token(tmp_path):
    pairing.save(str(tmp_path / "token.json"), backend_url=URL, credentials=Credentials("pi-01", "tok-1"))
    config = _config(tmp_path, publish_enabled=True)
    with TestClient(create_app(config)) as client:
        pub = client.app.state.publisher
        assert isinstance(pub, Publisher)
        assert pub._device_id == "pi-01" and pub._token == "tok-1"


def test_startup_without_token_or_code_explains_pairing(tmp_path):
    config = _config(tmp_path, publish_enabled=True, device_id="pi-01")
    with pytest.raises(ValueError, match="PAIRING_CODE"):
        with TestClient(create_app(config)):
            pass
