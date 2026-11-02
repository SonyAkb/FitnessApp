"""Тесты device/bus/factory.py: ветвление mock/real и ленивый импорт smbus2."""

import sys
import types

import pytest

from device.bus.factory import create_bus
from device.bus.fake_smbus import FakeSMBus
from device.config import load_config


def test_mock_mode_returns_fake_smbus_without_importing_smbus2(monkeypatch):
    monkeypatch.delenv("SENSOR_MODE", raising=False)
    monkeypatch.delitem(sys.modules, "smbus2", raising=False)

    config = load_config()
    bus = create_bus(config)

    assert isinstance(bus, FakeSMBus)
    assert "smbus2" not in sys.modules


def test_real_mode_imports_smbus2_lazily_inside_create_bus(monkeypatch):
    monkeypatch.setenv("SENSOR_MODE", "real")
    monkeypatch.setenv("I2C_BUS", "1")
    monkeypatch.delitem(sys.modules, "smbus2", raising=False)

    created_with = {}

    class _FakeRealSMBus:
        def __init__(self, bus_number):
            created_with["bus_number"] = bus_number

    fake_smbus2_module = types.ModuleType("smbus2")
    fake_smbus2_module.SMBus = _FakeRealSMBus
    monkeypatch.setitem(sys.modules, "smbus2", fake_smbus2_module)

    config = load_config()
    bus = create_bus(config)

    assert isinstance(bus, _FakeRealSMBus)
    assert created_with["bus_number"] == 1


def test_unknown_sensor_mode_raises_value_error(monkeypatch):
    monkeypatch.setenv("SENSOR_MODE", "weird")

    config = load_config()

    with pytest.raises(ValueError):
        create_bus(config)
