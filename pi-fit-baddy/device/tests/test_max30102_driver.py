"""Тесты драйвера Max30102 (PI-05) поверх FakeSMBus + VirtualMax30102.

Виртуальный чип пополняет FIFO по чтению FIFO_WR_PTR (PI-03), а драйвер его
не читает (ради единственного блочного чтения FIFO_DATA), поэтому "ход
времени" в тестах моделируется прямым чтением WR_PTR через шину.
"""

from __future__ import annotations

import pytest

from device.bus.fake_smbus import FakeSMBus
from device.drivers.max30102 import Max30102
from device.virtual.max30102 import VirtualMax30102

ADDR = 0x57


def _make(samples: list[tuple[int, int]] | None = None):
    # Источник чипа отдаёт (ir, red); драйвер возвращает (red, ir).
    source = iter(samples) if samples is not None else iter(lambda: (1, 2), None)
    bus = FakeSMBus()
    bus.register_device(ADDR, VirtualMax30102(source))
    return bus, Max30102(bus, ADDR)


def _produce(drv: Max30102, n: int) -> None:
    for _ in range(n):
        drv.available_samples()  # на виртуальном чипе чтение WR_PTR пополняет FIFO


def test_part_id():
    _, drv = _make()
    assert drv.part_id() == 0x15


def test_initialize_clears_shdn_preserving_other_bits():
    bus, drv = _make()
    bus.write_byte_data(ADDR, 0x09, 0x80 | 0x03)
    drv.initialize()
    assert bus.read_byte_data(ADDR, 0x09) == 0x03


def test_shutdown_chip_produces_nothing_until_initialize():
    bus, drv = _make([(10, 20), (11, 21)])
    bus.write_byte_data(ADDR, 0x09, 0x80)
    _produce(drv, 3)
    assert drv.read_fifo_samples(1) == [(0, 0)]
    drv.initialize()
    _produce(drv, 2)
    assert drv.read_fifo_samples(2) == [(20, 10), (21, 11)]


def test_read_fifo_samples_parses_several_samples():
    src = [(100, 200), (0x3FFFF, 5), (70000, 130000)]
    _bus, drv = _make(src)
    drv.initialize()
    _produce(drv, 4)  # последний вызов уже ничего не добавляет: источник пуст
    assert drv.read_fifo_samples(3) == [(red, ir) for ir, red in src]


def test_available_samples_reports_pointer_difference_and_matches_read():
    src = [(1, 2), (3, 4), (5, 6), (7, 8)]
    _, drv = _make(src)
    drv.initialize()
    _produce(drv, 3)
    # WR_PTR читается до пополнения: три предыдущих чтения дали 3 отсчёта.
    assert drv.available_samples() == 3
    assert drv.read_fifo_samples(3) == [(red, ir) for ir, red in src[:3]]


def test_available_samples_is_zero_on_empty_fifo():
    _, drv = _make()
    assert drv.available_samples() == 0


def test_available_samples_wraps_modulo_32():
    _, drv = _make()
    drv.initialize()
    _produce(drv, 20)
    drv.read_fifo_samples(20)
    _produce(drv, 20)  # WR_PTR = 40 % 32 = 8, RD_PTR = 20
    assert drv.available_samples() == 20


class _StubBus:
    def __init__(self, block: list[int]) -> None:
        self._block = block

    def write_byte_data(self, addr: int, reg: int, val: int) -> None:
        pass

    def read_byte_data(self, addr: int, reg: int) -> int:
        return 0

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list[int]:
        return list(self._block[:length])


def test_channel_values_masked_to_18_bits():
    # старшие 6 бит контейнера (биты 23..18) выставлены — должны отброситься
    drv = Max30102(_StubBus([0xFF, 0xFF, 0xFF, 0xFC, 0x00, 0x01]), ADDR)
    assert drv.read_fifo_samples(1) == [(0x03FFFF, 0x000001)]


def test_read_fifo_samples_zero_count():
    _, drv = _make()
    assert drv.read_fifo_samples(0) == []


def test_overflow_count_grows_when_fifo_not_drained():
    _bus, drv = _make()
    drv.initialize()
    assert drv.overflow_count() == 0
    _produce(drv, 40)
    assert drv.overflow_count() > 0


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.part_id(),
        lambda d: d.initialize(),
        lambda d: d.read_fifo_samples(1),
        lambda d: d.overflow_count(),
    ],
)
def test_wrong_address_raises_oserror(call):
    bus, _ = _make()
    drv = Max30102(bus, 0x58)
    with pytest.raises(OSError) as exc:
        call(drv)
    assert exc.value.errno == 121
