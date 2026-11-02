"""Единственная точка ветвления mock/real для шины I2C (docs/pi.md §3.1).

`SENSOR_MODE=mock` (по умолчанию) → `FakeSMBus`, `smbus2` не импортируется
вообще. `SENSOR_MODE=real` → `smbus2` импортируется лениво, внутри вызова
`create_bus`, а не при импорте этого модуля — на Mac/Linux без платы модуль
`factory.py` можно импортировать без установленного `smbus2`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from device.bus.fake_smbus import FakeSMBus
from device.config import Config

if TYPE_CHECKING:
    import smbus2


def create_bus(config: Config) -> FakeSMBus | smbus2.SMBus:
    """Создаёт шину I2C согласно `config.sensor_mode`.

    `mock` → `FakeSMBus` с виртуальными чипами (`build_mock_bus`). `real` → ленивый `import smbus2`,
    `smbus2.SMBus(config.i2c_bus)`.
    """
    if config.sensor_mode == "mock":
        from device.virtual.mock_bus import build_mock_bus  # только в mock

        return build_mock_bus(config)
    if config.sensor_mode == "real":
        import smbus2  # лениво: не установлен и не нужен в режиме mock

        return smbus2.SMBus(config.i2c_bus)
    raise ValueError(f"Неизвестный SENSOR_MODE: {config.sensor_mode!r}")
