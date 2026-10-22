"""Тесты device/virtual/mock_bus.py: сборка mock-шины с виртуальными чипами."""

import dataclasses

import pytest

from device.bus.factory import create_bus
from device.bus.fake_smbus import FakeSMBus
from device.config import load_config
from device.drivers.max30102 import Max30102
from device.drivers.mpu6050 import Mpu6050
from device.virtual.mock_bus import build_mock_bus


def _config(**overrides):
    return dataclasses.replace(load_config(), sensor_mode="mock", **overrides)


def test_create_bus_mock_registers_both_chips():
    config = _config(scenario="walk")
    bus = create_bus(config)

    assert isinstance(bus, FakeSMBus)
    assert Mpu6050(bus, config.mpu6050_addr).who_am_i() == 0x68
    assert Max30102(bus, config.max30102_addr).part_id() == 0x15


def test_builtin_scenario_is_looped_beyond_duration():
    config = _config(scenario="walk", sample_rate_hz=10.0)
    bus = build_mock_bus(config)
    mpu = Mpu6050(bus, config.mpu6050_addr)
    mpu.wake()

    # walk идёт 60 с = 600 отсчётов; читаем в два раза больше
    samples = [mpu.read_acceleration_g() for _ in range(1300)]

    assert any(abs(s[0]) > 1.2 for s in samples[-100:])  # всплески шагов после петли


def test_csv_scenario_is_read_and_looped(tmp_path):
    prefix = tmp_path / "rec"
    (tmp_path / "rec_accel.csv").write_text("t,x,y,z\n0,0.5,0,0\n0.02,0.25,0,0\n")
    (tmp_path / "rec_ppg.csv").write_text("t,ir,red\n0,1000,500\n0.02,1100,600\n")
    config = _config(scenario=str(prefix))
    bus = build_mock_bus(config)

    mpu = Mpu6050(bus, config.mpu6050_addr)
    mpu.wake()
    xs = [round(mpu.read_acceleration_g()[0], 2) for _ in range(4)]
    assert xs == [0.5, 0.25, 0.5, 0.25]

    chip = Max30102(bus, config.max30102_addr)
    chip.initialize()
    got = []
    for _ in range(5):
        n = chip.available_samples()
        got.extend(chip.read_fifo_samples(n))
    assert got[:3] == [(500, 1000), (600, 1100), (500, 1000)]


def test_missing_csv_fails_fast(tmp_path):
    config = _config(scenario=str(tmp_path / "nope"))

    with pytest.raises(FileNotFoundError):
        build_mock_bus(config)

