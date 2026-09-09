"""`FakeSMBus` — эмуляция шины I2C с тем же интерфейсом, что у `smbus2.SMBus`.

Используется в режиме `SENSOR_MODE=mock` (см. `device/bus/factory.py`) и как
опора для виртуальных чипов `VirtualMPU6050`/`VirtualMax30102` (PI-02/PI-03):
они регистрируются на шине по адресу и реализуют те же три метода без
аргумента `addr`, который берёт на себя сама шина.

Обращение к адресу без зарегистрированного устройства ведёт себя как
реальная шина без ответа: `OSError(121, "Remote I/O error")`
(docs/pi.md §6).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RegisterDevice(Protocol):
    """Интерфейс устройства, которое регистрируется на `FakeSMBus` по адресу."""

    def write_byte_data(self, reg: int, val: int) -> None: ...

    def read_byte_data(self, reg: int) -> int: ...

    def read_i2c_block_data(self, reg: int, length: int) -> list[int]: ...


def _remote_io_error() -> OSError:
    return OSError(121, "Remote I/O error")


class FakeSMBus:
    """Эмуляция `smbus2.SMBus`: тот же набор методов, реестр устройств по адресу."""

    def __init__(self) -> None:
        self._devices: dict[int, RegisterDevice] = {}

    def register_device(self, addr: int, device: RegisterDevice) -> None:
        """Регистрирует виртуальный чип `device` по адресу `addr` на шине."""
        if addr in self._devices:
            raise ValueError(f"Устройство уже зарегистрировано на адресе {addr!r}")
        self._devices[addr] = device

    def _get_device(self, addr: int) -> RegisterDevice:
        try:
            return self._devices[addr]
        except KeyError:
            raise _remote_io_error() from None

    def write_byte_data(self, addr: int, reg: int, val: int) -> None:
        self._get_device(addr).write_byte_data(reg, val)

    def read_byte_data(self, addr: int, reg: int) -> int:
        return self._get_device(addr).read_byte_data(reg)

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list[int]:
        return self._get_device(addr).read_i2c_block_data(reg, length)
