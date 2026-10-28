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


# Предел блочного чтения настоящего smbus2 (I2C_SMBUS_BLOCK_MAX): длиннее —
# ValueError("Desired block length over 32 bytes"). Эмуляция обязана давать
# ту же ошибку, что и железо (docs/pi.md §3 правило 5), иначе драйвер, который
# в mock читает больше, упадёт только на плате.
# https://github.com/kplindegaard/smbus2 (smbus2.SMBus.read_i2c_block_data)
_SMBUS_BLOCK_MAX = 32


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
        if length > _SMBUS_BLOCK_MAX:
            raise ValueError(f"Desired block length over {_SMBUS_BLOCK_MAX} bytes")
        return self._get_device(addr).read_i2c_block_data(reg, length)
