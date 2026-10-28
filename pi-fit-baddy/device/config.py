"""Конфигурация узла Pi — единственный источник настроек для всех задач PI-02…PI-10.

Значения читаются из переменных окружения; дефолты соответствуют таблице
"Конфигурация" в `pi-fit-baddy/README.md` и требованиям `docs/pi.md` §3.7-3.8.
Модуль не импортирует `smbus2`/`gpiozero` — ветвление mock/real живёт только
в `device/bus/factory.py`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_str(name: str, default: str | None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value, 0)  # int(..., 0) понимает и "0x68", и обычные "17"


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return float(value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    """Снимок конфигурации узла на момент запуска процесса."""

    sensor_mode: str
    i2c_bus: int
    mpu6050_addr: int
    max30102_addr: int
    max30102_int_pin: int
    gpiozero_pin_factory: str | None
    sample_rate_hz: float
    step_threshold_g: float
    step_min_interval_ms: int
    step_smoothing_samples: int
    hr_band_hz_low: float
    hr_band_hz_high: float
    hr_window_s: float
    hr_min_signal_ratio: float
    history_max_points: int
    battery_percent: int
    scenario: str
    backend_url: str | None
    device_id: str | None
    device_token: str | None
    pairing_code: str | None
    device_token_file: str
    publish_enabled: bool
    publish_interval_seconds: int
    calories_per_step: float


def load_config() -> Config:
    """Собирает `Config` из переменных окружения (см. README → "Конфигурация").

    SAMPLE_RATE_HZ, STEP_THRESHOLD_G, STEP_MIN_INTERVAL_MS, HR_BAND_HZ_LOW,
    HR_BAND_HZ_HIGH, HR_WINDOW_S и HR_MIN_SIGNAL_RATIO не подтверждены даташитом или калибровкой —
    это стартовые значения для синтетики, подбираются на реальном железе
    в PI-10 (docs/pi.md §3.8: "параметры алгоритмов... будут подбираться
    на реальном железе").
    """

    return Config(
        sensor_mode=_env_str("SENSOR_MODE", "mock").strip().lower(),
        i2c_bus=_env_int("I2C_BUS", 1),
        mpu6050_addr=_env_int("MPU6050_ADDR", 0x68),
        max30102_addr=_env_int("MAX30102_ADDR", 0x57),
        max30102_int_pin=_env_int("MAX30102_INT_PIN", 17),
        gpiozero_pin_factory=_env_str("GPIOZERO_PIN_FACTORY", None),
        sample_rate_hz=_env_float("SAMPLE_RATE_HZ", 50.0),
        step_threshold_g=_env_float("STEP_THRESHOLD_G", 0.15),
        step_min_interval_ms=_env_int("STEP_MIN_INTERVAL_MS", 300),
        step_smoothing_samples=_env_int("STEP_SMOOTHING_SAMPLES", 3),
        hr_band_hz_low=_env_float("HR_BAND_HZ_LOW", 0.5),
        hr_band_hz_high=_env_float("HR_BAND_HZ_HIGH", 4.0),
        hr_window_s=_env_float("HR_WINDOW_S", 5.0),
        hr_min_signal_ratio=_env_float("HR_MIN_SIGNAL_RATIO", 0.01),
        history_max_points=_env_int("HISTORY_MAX_POINTS", 3600),
        battery_percent=_env_int("BATTERY_PERCENT", 82),
        scenario=_env_str("SCENARIO", "walk"),
        backend_url=_env_str("BACKEND_URL", None),
        device_id=_env_str("DEVICE_ID", None),
        device_token=_env_str("DEVICE_TOKEN", None),
        pairing_code=_env_str("PAIRING_CODE", None),
        device_token_file=_env_str("DEVICE_TOKEN_FILE", ".device_token.json"),
        publish_enabled=_env_bool("PUBLISH_ENABLED", False),
        publish_interval_seconds=_env_int("PUBLISH_INTERVAL_SECONDS", 5),
        calories_per_step=_env_float("CALORIES_PER_STEP", 0.04),
    )
