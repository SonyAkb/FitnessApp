"""Тесты device/config.py: дефолты и парсинг переменных окружения."""

import sys

from device.config import load_config

_ALL_VARS = [
    "SENSOR_MODE",
    "I2C_BUS",
    "MPU6050_ADDR",
    "MAX30102_ADDR",
    "MAX30102_INT_PIN",
    "GPIOZERO_PIN_FACTORY",
    "SAMPLE_RATE_HZ",
    "STEP_THRESHOLD_G",
    "STEP_MIN_INTERVAL_MS",
    "STEP_SMOOTHING_SAMPLES",
    "HR_BAND_HZ_LOW",
    "HR_BAND_HZ_HIGH",
    "HR_WINDOW_S",
    "HR_MIN_SIGNAL_RATIO",
    "HISTORY_MAX_POINTS",
    "BATTERY_PERCENT",
    "SCENARIO",
    "BACKEND_URL",
    "DEVICE_ID",
    "DEVICE_TOKEN",
    "PAIRING_CODE",
    "DEVICE_TOKEN_FILE",
    "PUBLISH_ENABLED",
    "PUBLISH_INTERVAL_SECONDS",
    "CALORIES_PER_STEP",
]


def _clear_env(monkeypatch):
    for name in _ALL_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_when_env_not_set(monkeypatch):
    _clear_env(monkeypatch)

    config = load_config()

    assert config.sensor_mode == "mock"
    assert config.i2c_bus == 1
    assert config.mpu6050_addr == 0x68
    assert config.max30102_addr == 0x57
    assert config.max30102_int_pin == 17
    assert config.gpiozero_pin_factory is None
    assert config.sample_rate_hz == 50.0
    assert config.step_threshold_g == 0.15
    assert config.step_min_interval_ms == 300
    assert config.step_smoothing_samples == 3
    assert config.hr_band_hz_low == 0.5
    assert config.hr_band_hz_high == 4.0
    assert config.hr_window_s == 5.0
    assert config.hr_min_signal_ratio == 0.01
    assert config.history_max_points == 3600
    assert config.battery_percent == 82
    assert config.scenario == "walk"
    assert config.backend_url is None
    assert config.device_id is None
    assert config.device_token is None
    assert config.publish_enabled is False
    assert config.publish_interval_seconds == 5
    assert config.calories_per_step == 0.04


def test_smbus2_not_imported_by_default(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.delitem(sys.modules, "smbus2", raising=False)

    load_config()

    assert "smbus2" not in sys.modules


def test_env_overrides_are_applied(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("SENSOR_MODE", "REAL")
    monkeypatch.setenv("I2C_BUS", "3")
    monkeypatch.setenv("MPU6050_ADDR", "0x69")
    monkeypatch.setenv("PUBLISH_ENABLED", "true")
    monkeypatch.setenv("SAMPLE_RATE_HZ", "100")
    monkeypatch.setenv("STEP_SMOOTHING_SAMPLES", "5")
    monkeypatch.setenv("HR_MIN_SIGNAL_RATIO", "0.05")

    config = load_config()

    assert config.sensor_mode == "real"
    assert config.i2c_bus == 3
    assert config.mpu6050_addr == 0x69
    assert config.publish_enabled is True
    assert config.sample_rate_hz == 100.0
    assert config.step_smoothing_samples == 5
    assert config.hr_min_signal_ratio == 0.05


def test_device_token_has_no_default_value(monkeypatch):
    _clear_env(monkeypatch)

    config = load_config()

    assert config.device_token is None
