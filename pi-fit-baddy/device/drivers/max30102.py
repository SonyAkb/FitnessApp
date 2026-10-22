"""Драйвер пульсоксиметра MAX30102 (PI-05).

Шина и адрес приходят через конструктор; используются только
`write_byte_data`, `read_byte_data`, `read_i2c_block_data` (docs/pi.md §3
правило 2). Проверок режима mock/real здесь нет.

Источник регистров — даташит Analog Devices (Maxim) MAX30102:
https://wcm-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf
"""

from __future__ import annotations

from typing import Any

_REG_FIFO_WR_PTR = 0x04
_REG_OVF_COUNTER = 0x05
_REG_FIFO_DATA = 0x07
_REG_MODE_CONFIG = 0x09
_REG_PART_ID = 0xFF

_FIFO_DEPTH = 32

_SHDN_BIT = 0x80  # MODE_CONFIG, бит 7

# Формат отсчёта: 3 байта на канал, RED затем IR, big-endian, 18 бит значимых —
# тот же провизорный порядок, что и в виртуальном чипе PI-03.
# TODO(datasheet): сверить порядок RED/IR по разделу FIFO Data Register
# и проверить на реальной плате (PI-10).
_BYTES_PER_CHANNEL = 3
_BYTES_PER_SAMPLE = 2 * _BYTES_PER_CHANNEL
# smbus2.SMBus.read_i2c_block_data бросает ValueError при length > 32. Читаем
# кусками по 30 байт (5 отсчётов): кратно 6, отсчёт не рвётся между кусками.
_MAX_SAMPLES_PER_READ = 5
_SAMPLE_VALUE_MASK = 0x03FFFF


class Max30102:
    def __init__(self, bus: Any, addr: int) -> None:
        self._bus = bus
        self._addr = addr

    def part_id(self) -> int:
        return self._bus.read_byte_data(self._addr, _REG_PART_ID)

    def initialize(self) -> None:
        """Сбрасывает бит SHDN в MODE_CONFIG, сохраняя остальные биты.

        SPO2_CONFIG/FIFO_CONFIG намеренно не настраиваются: виртуальный чип
        (PI-03) их не моделирует, а выдумывать биты без даташита нельзя
        (docs/pi.md §4).

        TODO(datasheet): на реальной плате нужно ещё настроить биты режима
        MODE_CONFIG[2:0], SPO2_CONFIG, FIFO_CONFIG и токи светодиодов
        (LED1_PA/LED2_PA). Значения не подтверждены по даташиту и не
        проверяются моком, поэтому не выдуманы здесь; делается и проверяется
        на реальной плате в PI-10.
        """
        value = self._bus.read_byte_data(self._addr, _REG_MODE_CONFIG)
        self._bus.write_byte_data(
            self._addr, _REG_MODE_CONFIG, value & ~_SHDN_BIT & 0xFF
        )

    def read_fifo_samples(self, count: int) -> list[tuple[int, int]]:
        """Читает ровно `count` отсчётов `(red, ir)` блочными чтениями.

        Не более 5 отсчётов (30 байт) за транзакцию — лимит smbus2 в 32 байта.
        Драйвер не знает, сколько отсчётов реально есть: сначала вызывайте
        `available_samples()`. При пустом FIFO или при выставленном SHDN
        вернутся пары (0, 0).

        Число доступных отсчётов не определяется: разница FIFO_WR_PTR и
        FIFO_RD_PTR (5 бит, mod 32) не отличает пустую очередь от полной
        (неоднозначность и у настоящего чипа, см. PI-03).
        """
        if count <= 0:
            return []
        data: list[int] = []
        remaining = count
        while remaining > 0:
            chunk = min(remaining, _MAX_SAMPLES_PER_READ)
            data.extend(
                self._bus.read_i2c_block_data(
                    self._addr, _REG_FIFO_DATA, _BYTES_PER_SAMPLE * chunk
                )
            )
            remaining -= chunk
        samples: list[tuple[int, int]] = []
        for i in range(count):
            base = i * _BYTES_PER_SAMPLE
            red = self._channel(data, base)
            ir = self._channel(data, base + _BYTES_PER_CHANNEL)
            samples.append((red, ir))
        return samples

    def available_samples(self) -> int:
        """Число непрочитанных отсчётов: `(FIFO_WR_PTR - FIFO_RD_PTR) % 32`.

        WR_PTR, OVF_COUNTER и RD_PTR идут подряд (0x04-0x06), поэтому читаются
        одной транзакцией: два отдельных чтения на реальном железе могут
        разойтись с записью чипа. На реальном железе чтение
        WR_PTR побочных эффектов не имеет; виртуальный чип (PI-03) при каждом
        чтении WR_PTR пополняет FIFO на один отсчёт и возвращает значение
        указателя до этого пополнения. Код драйвера одинаков в обоих режимах.

        Результат 0 неоднозначен: "пусто" или "ровно 32 непрочитанных"
        (5-битные указатели по модулю 32, так же и на настоящем чипе).
        Здесь это не разрешается.
        """
        block = self._bus.read_i2c_block_data(self._addr, _REG_FIFO_WR_PTR, 3)
        return (block[0] - block[2]) % _FIFO_DEPTH

    def overflow_count(self) -> int:
        return self._bus.read_byte_data(self._addr, _REG_OVF_COUNTER)

    @staticmethod
    def _channel(data: list[int], offset: int) -> int:
        value = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2]
        return value & _SAMPLE_VALUE_MASK
