"""Сборка шины для `SENSOR_MODE=mock`: `FakeSMBus` + виртуальные чипы (PI-08).

Вызывается только из `device/bus/factory.py` — единственной точки ветвления
mock/real. Источник данных выбирается по `config.scenario`: имя встроенного
сценария (`SCENARIOS`) либо префикс CSV-записи (`<prefix>_accel.csv`,
`<prefix>_ppg.csv`).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Iterator

from device.bus.fake_smbus import FakeSMBus
from device.config import Config
from device.virtual.csv_player import accel_samples_from_csv, ppg_samples_from_csv
from device.virtual.mpu6050 import VirtualMPU6050
from device.virtual.max30102 import VirtualMax30102
from device.virtual.scenarios import SCENARIOS, resolve_scenario
from device.virtual.signals import accel_samples, ppg_samples


def _looped(make_stream: Callable[[], Iterator]) -> Iterator:
    """Бесконечный поток: по исчерпании сценарий начинается заново.

    Собственное решение: виртуальные чипы при исчерпании источника замирают
    (MPU повторяет последний отсчёт, MAX30102 перестаёт пополняться), а
    сервис должен работать дольше `duration_s` сценария.
    """
    while True:
        yield from make_stream()


def build_mock_bus(config: Config) -> FakeSMBus:
    """Собирает `FakeSMBus` с `VirtualMPU6050` и `VirtualMax30102`.

    Несуществующий/пустой CSV даёт ошибку сразу при сборке (быстрый отказ).
    """
    if config.scenario in SCENARIOS:
        segment = resolve_scenario(config.scenario)
        rate = config.sample_rate_hz
        accel = _looped(lambda: accel_samples(segment, rate))
        ppg = _looped(lambda: ppg_samples(segment, rate))  # порядок (ir, red)
    else:
        prefix = config.scenario
        # Читаются сразу (ошибка при сборке), затем зацикливаются по списку.
        accel_rows = [(x, y, z) for _t, x, y, z in accel_samples_from_csv(prefix)]
        ppg_rows = [(ir, red) for _t, ir, red in ppg_samples_from_csv(prefix)]
        accel = itertools.cycle(accel_rows)
        ppg = itertools.cycle(ppg_rows)

    bus = FakeSMBus()
    bus.register_device(config.mpu6050_addr, VirtualMPU6050(accel))
    bus.register_device(config.max30102_addr, VirtualMax30102(ppg))
    return bus
