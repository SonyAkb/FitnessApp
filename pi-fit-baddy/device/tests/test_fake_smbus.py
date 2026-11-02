"""Тесты device/bus/fake_smbus.py: реестр устройств и ошибка неизвестного адреса."""

import pytest

from device.bus.fake_smbus import FakeSMBus


class _StubDevice:
    """Тестовый дубль виртуального чипа — интерфейс RegisterDevice."""

    def __init__(self) -> None:
        self.registers: dict[int, int] = {}

    def write_byte_data(self, reg: int, val: int) -> None:
        self.registers[reg] = val

    def read_byte_data(self, reg: int) -> int:
        return self.registers.get(reg, 0)

    def read_i2c_block_data(self, reg: int, length: int) -> list[int]:
        return [self.registers.get(reg + i, 0) for i in range(length)]


def test_known_address_write_then_read_roundtrip():
    bus = FakeSMBus()
    bus.register_device(0x68, _StubDevice())

    bus.write_byte_data(0x68, 0x10, 42)

    assert bus.read_byte_data(0x68, 0x10) == 42


def test_known_address_block_read_reflects_writes():
    bus = FakeSMBus()
    bus.register_device(0x57, _StubDevice())

    bus.write_byte_data(0x57, 0x07, 1)
    bus.write_byte_data(0x57, 0x08, 2)

    assert bus.read_i2c_block_data(0x57, 0x07, 2) == [1, 2]


def test_register_device_on_occupied_address_raises_value_error():
    bus = FakeSMBus()
    bus.register_device(0x68, _StubDevice())

    with pytest.raises(ValueError):
        bus.register_device(0x68, _StubDevice())


def test_two_devices_on_different_addresses_do_not_interfere():
    bus = FakeSMBus()
    bus.register_device(0x68, _StubDevice())
    bus.register_device(0x57, _StubDevice())

    bus.write_byte_data(0x68, 0x00, 11)
    bus.write_byte_data(0x57, 0x00, 22)

    assert bus.read_byte_data(0x68, 0x00) == 11
    assert bus.read_byte_data(0x57, 0x00) == 22


def test_unknown_address_read_raises_remote_io_error():
    bus = FakeSMBus()

    with pytest.raises(OSError) as exc_info:
        bus.read_byte_data(0x68, 0x00)

    assert exc_info.value.errno == 121
    assert exc_info.value.strerror == "Remote I/O error"


def test_unknown_address_write_raises_remote_io_error():
    bus = FakeSMBus()

    with pytest.raises(OSError) as exc_info:
        bus.write_byte_data(0x68, 0x00, 1)

    assert exc_info.value.errno == 121


def test_unknown_address_block_read_raises_remote_io_error():
    bus = FakeSMBus()

    with pytest.raises(OSError) as exc_info:
        bus.read_i2c_block_data(0x68, 0x00, 6)

    assert exc_info.value.errno == 121


def test_block_read_over_32_bytes_raises_like_smbus2():
    bus = FakeSMBus()
    bus.register_device(0x68, _StubDevice())

    assert len(bus.read_i2c_block_data(0x68, 0x00, 32)) == 32

    with pytest.raises(ValueError):
        bus.read_i2c_block_data(0x68, 0x00, 33)
