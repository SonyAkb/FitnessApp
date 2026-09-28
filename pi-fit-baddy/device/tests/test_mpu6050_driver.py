"""Тесты драйвера Mpu6050 (PI-05) поверх FakeSMBus + VirtualMPU6050."""

from __future__ import annotations

import itertools

import pytest

from device.bus.fake_smbus import FakeSMBus
from device.drivers.mpu6050 import Mpu6050
from device.virtual.mpu6050 import VirtualMPU6050

ADDR = 0x68
SAMPLE = (0.5, -0.25, 1.0)


def _make() -> tuple[FakeSMBus, Mpu6050]:
    bus = FakeSMBus()
    bus.register_device(ADDR, VirtualMPU6050(itertools.repeat(SAMPLE)))
    return bus, Mpu6050(bus, ADDR)


def test_who_am_i():
    _, drv = _make()
    assert drv.who_am_i() == 0x68


def test_read_without_wake_returns_zeros():
    _, drv = _make()
    assert drv.read_acceleration_g() == (0.0, 0.0, 0.0)


def test_wake_then_read_returns_source_values():
    _, drv = _make()
    drv.wake()
    assert drv.read_acceleration_g() == pytest.approx(SAMPLE, abs=1 / 16384)


def test_wake_preserves_other_pwr_mgmt_bits():
    bus, drv = _make()
    bus.write_byte_data(ADDR, 0x6B, 0x40 | 0x01)
    drv.wake()
    assert bus.read_byte_data(ADDR, 0x6B) == 0x01


@pytest.mark.parametrize("code,lsb", [(0, 16384), (1, 8192), (2, 4096), (3, 2048)])
def test_set_range_keeps_same_g_value(code: int, lsb: int):
    bus, drv = _make()
    drv.wake()
    drv.set_range(code)
    assert (bus.read_byte_data(ADDR, 0x1C) >> 3) & 0b11 == code
    assert drv.read_acceleration_g() == pytest.approx(SAMPLE, abs=1 / lsb)


def test_set_range_preserves_other_accel_config_bits():
    bus, drv = _make()
    bus.write_byte_data(ADDR, 0x1C, 0xE0)
    drv.set_range(2)
    assert bus.read_byte_data(ADDR, 0x1C) == 0xE0 | (2 << 3)


def test_set_range_rejects_invalid_code():
    _, drv = _make()
    with pytest.raises(ValueError):
        drv.set_range(4)


def test_negative_values_decoded_signed():
    bus = FakeSMBus()
    bus.register_device(ADDR, VirtualMPU6050(itertools.repeat((-1.0, -0.5, 0.0))))
    drv = Mpu6050(bus, ADDR)
    drv.wake()
    assert drv.read_acceleration_g() == pytest.approx((-1.0, -0.5, 0.0), abs=1e-4)


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.who_am_i(),
        lambda d: d.wake(),
        lambda d: d.set_range(1),
        lambda d: d.read_acceleration_g(),
    ],
)
def test_wrong_address_raises_oserror(call):
    bus, _ = _make()
    drv = Mpu6050(bus, 0x69)
    with pytest.raises(OSError) as exc:
        call(drv)
    assert exc.value.errno == 121


def test_negative_axes_and_int16_boundary_decoded_with_sign():
    bus = FakeSMBus()
    src = itertools.repeat((-0.5, -1.999, 1.999))
    bus.register_device(ADDR, VirtualMPU6050(src))
    drv = Mpu6050(bus, ADDR)
    drv.wake()
    x, y, z = drv.read_acceleration_g()
    assert x == pytest.approx(-0.5, abs=1 / 16384)
    assert y == pytest.approx(-1.999, abs=1 / 16384)
    assert z == pytest.approx(1.999, abs=1 / 16384)
    assert y < 0 < z


def test_driver_reads_preconfigured_range_on_first_read():
    bus = FakeSMBus()
    bus.register_device(ADDR, VirtualMPU6050(itertools.repeat(SAMPLE)))
    bus.write_byte_data(ADDR, 0x1C, 3 << 3)  # чип уже в ±16g до создания драйвера
    drv = Mpu6050(bus, ADDR)
    drv.wake()
    assert drv.read_acceleration_g() == pytest.approx(SAMPLE, abs=1 / 2048)
