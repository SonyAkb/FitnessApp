"""Тесты device/virtual/mpu6050.py: VirtualMPU6050 — сон, диапазон,
формат данных, побайтовое чтение, исчерпание источника, немоделируемые
регистры. Acceptance Criteria — спека PI-02
(_bmad-output/implementation-artifacts/spec-pi-02-virtual-mpu6050.md).
"""

from __future__ import annotations

import itertools

from device.virtual.mpu6050 import VirtualMPU6050

_WHO_AM_I = 0x75
_PWR_MGMT_1 = 0x6B
_ACCEL_CONFIG = 0x1C
_ACCEL_XOUT_H = 0x3B
_GYRO_CONFIG_UNMODELED = 0x1B

_AFS_SEL_0_2G = 0b0000_0000
_AFS_SEL_1_4G = 0b0000_1000
_AFS_SEL_2_8G = 0b0001_0000
_AFS_SEL_3_16G = 0b0001_1000

_LSB_PER_G_2G = 16384
_LSB_PER_G_4G = 8192
_LSB_PER_G_8G = 4096
_LSB_PER_G_16G = 2048


def _wake(chip: VirtualMPU6050) -> None:
    chip.write_byte_data(_PWR_MGMT_1, 0x00)


def _to_signed_int16(high_byte: int, low_byte: int) -> int:
    value = (high_byte << 8) | low_byte
    if value >= 0x8000:
        value -= 0x10000
    return value


def _axes_from_block(block: list[int]) -> tuple[int, int, int]:
    x = _to_signed_int16(block[0], block[1])
    y = _to_signed_int16(block[2], block[3])
    z = _to_signed_int16(block[4], block[5])
    return x, y, z


def test_who_am_i_is_fixed_regardless_of_sleep_or_range():
    chip = VirtualMPU6050(itertools.repeat((0.0, 0.0, 0.0)))

    assert chip.read_byte_data(_WHO_AM_I) == 0x68

    _wake(chip)
    chip.write_byte_data(_ACCEL_CONFIG, _AFS_SEL_3_16G)

    assert chip.read_byte_data(_WHO_AM_I) == 0x68


def test_default_state_is_asleep_and_accel_block_reads_zero():
    chip = VirtualMPU6050(itertools.repeat((1.0, -1.0, 0.5)))

    block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)

    assert block == [0, 0, 0, 0, 0, 0]


def test_waking_up_returns_sample_scaled_by_current_range():
    chip = VirtualMPU6050(itertools.repeat((1.0, 0.5, -0.25)))

    _wake(chip)
    block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x, y, z = _axes_from_block(block)

    assert x == round(1.0 * _LSB_PER_G_2G)
    assert y == round(0.5 * _LSB_PER_G_2G)
    assert z == round(-0.25 * _LSB_PER_G_2G)


def test_changing_range_rescales_same_physical_signal_across_all_afs_sel_codes():
    # Один и тот же сигнал на каждом чтении (повторяющийся источник) —
    # меняется только AFS_SEL между ними. Проверяем все четыре кода, а не
    # только крайние 0 и 3, чтобы отловить регрессию в середине таблицы LSB/g.
    chip = VirtualMPU6050(itertools.repeat((1.0, 0.0, 0.0)))
    _wake(chip)

    block_2g = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x_2g, _, _ = _axes_from_block(block_2g)

    chip.write_byte_data(_ACCEL_CONFIG, _AFS_SEL_1_4G)
    block_4g = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x_4g, _, _ = _axes_from_block(block_4g)

    chip.write_byte_data(_ACCEL_CONFIG, _AFS_SEL_2_8G)
    block_8g = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x_8g, _, _ = _axes_from_block(block_8g)

    chip.write_byte_data(_ACCEL_CONFIG, _AFS_SEL_3_16G)
    block_16g = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x_16g, _, _ = _axes_from_block(block_16g)

    assert x_2g == round(1.0 * _LSB_PER_G_2G)
    assert x_4g == round(1.0 * _LSB_PER_G_4G)
    assert x_8g == round(1.0 * _LSB_PER_G_8G)
    assert x_16g == round(1.0 * _LSB_PER_G_16G)
    assert x_2g == x_16g * 8


def test_sample_beyond_full_scale_saturates_instead_of_wrapping():
    # 10.0g при AFS_SEL=0 (±2g, 16384 LSB/g) даёт raw = 163840, что далеко
    # за пределами int16 — ожидаем прижатие к 32767, а не переполнение
    # (Design Notes спеки: "значение прижимается к пределу, а не оборачивается").
    chip = VirtualMPU6050(itertools.repeat((10.0, -10.0, 0.0)))
    _wake(chip)

    block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x, y, _ = _axes_from_block(block)

    assert x == 32767
    assert y == -32768


def test_byte_by_byte_block_read_does_not_mix_two_different_samples():
    # Если бы чип тянул новый отсчёт на каждый отдельный байт, X пришёл бы
    # из первого отсчёта, а Y/Z — из второго.
    source = iter([(1.0, 0.5, -0.5), (-9.0, -9.0, -9.0)])
    chip = VirtualMPU6050(source)
    _wake(chip)

    byte_by_byte = [chip.read_byte_data(_ACCEL_XOUT_H + i) for i in range(6)]
    x, y, z = _axes_from_block(byte_by_byte)

    assert x == round(1.0 * _LSB_PER_G_2G)
    assert y == round(0.5 * _LSB_PER_G_2G)
    assert z == round(-0.5 * _LSB_PER_G_2G)


def test_exhausted_source_repeats_last_sample_without_raising():
    source = iter([(0.5, 0.0, 0.0)])
    chip = VirtualMPU6050(source)
    _wake(chip)

    first = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    second = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)  # источник уже пуст

    assert first == second
    x, _, _ = _axes_from_block(second)
    assert x == round(0.5 * _LSB_PER_G_2G)


def test_unmodeled_register_reads_zero_and_write_is_accepted_and_ignored():
    chip = VirtualMPU6050(itertools.repeat((0.0, 0.0, 0.0)))

    assert chip.read_byte_data(_GYRO_CONFIG_UNMODELED) == 0

    chip.write_byte_data(_GYRO_CONFIG_UNMODELED, 0x18)  # не должно поднять исключение

    assert chip.read_byte_data(_GYRO_CONFIG_UNMODELED) == 0


def test_pwr_mgmt_1_defaults_to_datasheet_reset_value_with_sleep_bit_set():
    chip = VirtualMPU6050(itertools.repeat((0.0, 0.0, 0.0)))

    assert chip.read_byte_data(_PWR_MGMT_1) == 0x40


def test_unmodeled_register_block_read_returns_zeros_and_write_is_accepted():
    chip = VirtualMPU6050(itertools.repeat((0.0, 0.0, 0.0)))

    assert chip.read_i2c_block_data(_GYRO_CONFIG_UNMODELED, 3) == [0, 0, 0]

    chip.write_byte_data(_GYRO_CONFIG_UNMODELED, 0x18)  # не должно поднять исключение

    assert chip.read_i2c_block_data(_GYRO_CONFIG_UNMODELED, 3) == [0, 0, 0]


def test_block_read_past_accel_range_returns_zero_for_out_of_range_bytes():
    # read_i2c_block_data(0x40, 2) выходит за ACCEL_ZOUT_L (0x40) в
    # немоделируемые регистры — тот же контракт "неизвестный регистр -> 0".
    chip = VirtualMPU6050(itertools.repeat((1.0, 0.0, 0.0)))
    _wake(chip)
    full_block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)  # заполняет кэш отсчётом
    accel_zout_l = full_block[5]

    block = chip.read_i2c_block_data(0x40, 2)

    assert block == [accel_zout_l, 0]


def test_sleeping_again_after_wake_zeroes_accel_block_again():
    chip = VirtualMPU6050(itertools.repeat((1.0, 0.0, 0.0)))
    _wake(chip)

    awake_block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    assert awake_block != [0, 0, 0, 0, 0, 0]

    chip.write_byte_data(_PWR_MGMT_1, 0x40)  # снова установить SLEEP
    asleep_again_block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)

    assert asleep_again_block == [0, 0, 0, 0, 0, 0]


def test_accel_config_stray_bits_do_not_corrupt_afs_sel_extraction():
    # Запись 0xFF в ACCEL_CONFIG выставляет все биты, включая зарезервированные
    # вне AFS_SEL (4:3) — диапазон должен извлекаться только из битов 4:3,
    # то есть 0b11 = AFS_SEL=3 (±16g).
    chip = VirtualMPU6050(itertools.repeat((1.0, 0.0, 0.0)))
    _wake(chip)

    chip.write_byte_data(_ACCEL_CONFIG, 0xFF)
    block = chip.read_i2c_block_data(_ACCEL_XOUT_H, 6)
    x, _, _ = _axes_from_block(block)

    assert x == round(1.0 * _LSB_PER_G_16G)
