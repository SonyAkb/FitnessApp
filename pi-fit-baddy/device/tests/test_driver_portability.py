"""Тест переносимости (PI-05): драйверы работают с любой шиной интерфейса
smbus2.SMBus, а не только с FakeSMBus (docs/pi.md §3 правило 2, §8)."""

from __future__ import annotations

import itertools

import pytest

from device.bus.fake_smbus import FakeSMBus
from device.drivers.max30102 import Max30102
from device.drivers.mpu6050 import Mpu6050
from device.virtual.max30102 import VirtualMax30102
from device.virtual.mpu6050 import VirtualMPU6050

MPU_ADDR = 0x68
MAX_ADDR = 0x57


class SpyBus:
    """Класс с ровно тремя методами smbus2.SMBus; оборачивает FakeSMBus и
    логирует вызовы. Не наследует FakeSMBus."""

    def __init__(self, inner: FakeSMBus) -> None:
        self._inner = inner
        self.calls: list[tuple] = []

    def write_byte_data(self, addr: int, reg: int, val: int) -> None:
        self.calls.append(("write_byte_data", addr, reg, val))
        self._inner.write_byte_data(addr, reg, val)

    def read_byte_data(self, addr: int, reg: int) -> int:
        self.calls.append(("read_byte_data", addr, reg))
        return self._inner.read_byte_data(addr, reg)

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list[int]:
        if length > 32:  # как smbus2.SMBus
            raise ValueError("Desired block length over 32 bytes")
        self.calls.append(("read_i2c_block_data", addr, reg, length))
        return list(self._inner.read_i2c_block_data(addr, reg, length))


def _fake_bus() -> FakeSMBus:
    bus = FakeSMBus()
    bus.register_device(
        MPU_ADDR, VirtualMPU6050(itertools.repeat((0.5, -0.25, 1.0)))
    )
    bus.register_device(
        MAX_ADDR, VirtualMax30102(iter([(10, 20), (11, 21), (12, 22)]))
    )
    return bus


def _run_scenario(bus) -> dict:
    mpu = Mpu6050(bus, MPU_ADDR)
    max_ = Max30102(bus, MAX_ADDR)
    result: dict = {"who": mpu.who_am_i(), "part": max_.part_id()}
    result["asleep"] = mpu.read_acceleration_g()
    mpu.wake()
    mpu.set_range(1)
    result["accel"] = mpu.read_acceleration_g()
    max_.initialize()
    for _ in range(3):  # "ход времени" виртуального чипа (PI-03)
        max_.available_samples()
    result["fifo"] = max_.read_fifo_samples(3)
    result["ovf"] = max_.overflow_count()
    return result


def test_drivers_give_same_results_through_spy_and_direct_bus():
    direct = _run_scenario(_fake_bus())
    spy = SpyBus(_fake_bus())
    via_spy = _run_scenario(spy)
    assert via_spy == direct
    assert via_spy["who"] == 0x68
    assert via_spy["asleep"] == (0.0, 0.0, 0.0)
    assert via_spy["fifo"] == [(20, 10), (21, 11), (22, 12)]


def test_drivers_use_only_smbus_interface_methods_and_block_reads():
    spy = SpyBus(_fake_bus())
    mpu = Mpu6050(spy, MPU_ADDR)
    max_ = Max30102(spy, MAX_ADDR)
    mpu.wake()
    mpu.read_acceleration_g()  # первое чтение один раз узнаёт диапазон
    spy.calls.clear()
    mpu.read_acceleration_g()
    assert spy.calls == [("read_i2c_block_data", MPU_ADDR, 0x3B, 6)]
    spy.calls.clear()
    max_.read_fifo_samples(4)
    assert spy.calls == [("read_i2c_block_data", MAX_ADDR, 0x07, 24)]


def test_oserror_propagates_unchanged_through_spy():
    spy = SpyBus(_fake_bus())
    with pytest.raises(OSError) as exc:
        Mpu6050(spy, 0x10).who_am_i()
    assert exc.value.errno == 121


@pytest.mark.parametrize("count", [6, 12])
def test_long_fifo_reads_are_chunked_within_smbus_limit(count: int):
    src = [(i + 1, 1000 + i) for i in range(count)]
    bus = FakeSMBus()
    bus.register_device(MAX_ADDR, VirtualMax30102(iter(src)))
    spy = SpyBus(bus)
    max_ = Max30102(spy, MAX_ADDR)
    max_.initialize()
    for _ in range(count):
        max_.available_samples()
    spy.calls.clear()
    assert max_.read_fifo_samples(count) == [(red, ir) for ir, red in src]
    lengths = [c[3] for c in spy.calls if c[0] == "read_i2c_block_data"]
    assert sum(lengths) == 6 * count
    assert max(lengths) <= 30
