"""Драйвер пульсоксиметра MAX30102 (PI-05).

Шина и адрес приходят через конструктор; используются только
`write_byte_data`, `read_byte_data`, `read_i2c_block_data` (docs/pi.md §3
правило 2). Проверок режима mock/real здесь нет.

Источник регистров — даташит Analog Devices (Maxim) MAX30102, 19-7740 Rev 1,
раздел "Register Maps and Descriptions" (стр. 10–21):
https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf
"""

from __future__ import annotations

import errno
from typing import Any

_REG_FIFO_WR_PTR = 0x04
_REG_OVF_COUNTER = 0x05
_REG_FIFO_RD_PTR = 0x06
_REG_FIFO_DATA = 0x07
_REG_FIFO_CONFIG = 0x08
_REG_MODE_CONFIG = 0x09
_REG_SPO2_CONFIG = 0x0A
_REG_LED1_PA = 0x0C  # красный (Table 9: LED1 = Red)
_REG_LED2_PA = 0x0D  # ИК (LED2 = IR)
_REG_PART_ID = 0xFF

_FIFO_DEPTH = 32

_RESET_BIT = 0x40  # MODE_CONFIG, бит 6; сбрасывается чипом сам после сброса (стр. 18)
_MODE_SPO2 = 0x03  # MODE[2:0] = 011: SpO2, красный + ИК (Table 4)

# FIFO_CONFIG = 0x00: SMP_AVE = 000 (без усреднения, Table 3), FIFO_ROLLOVER_EN = 0
# (полный FIFO не перезаписывается, потери видны в OVF_COUNTER), FIFO_A_FULL не используется.
_FIFO_CONFIG_VALUE = 0x00
# SPO2_CONFIG = 0x23: SPO2_ADC_RGE = 01 (4096 нА, Table 5), SPO2_SR = 000 (50 отсчётов/с,
# Table 6), LED_PW = 11 (411 мкс, 18 бит, Table 7); сочетание разрешено (Table 11).
# Частота 50 Гц выбрана по SAMPLE_RATE_HZ: чип не должен давать больше одного отсчёта
# за опрос, иначе HeartRateEstimator пропускает лишние (у них одна метка времени).
_SPO2_CONFIG_VALUE = 0x23
# Сколько раз перечитать MODE_CONFIG, ожидая, что чип сбросит бит RESET. Время сброса
# в даташите не указано; предел — собственное решение, проверяется на плате.
_RESET_POLL_ATTEMPTS = 100

# Формат отсчёта: 3 байта на канал, сначала RED, затем IR (Figure 2 и псевдокод
# чтения FIFO, стр. 15–16), данные выровнены влево: старший бит всегда в позиции 17
# (Table 1), при 18-битном разрешении значимы все 18 бит.
_BYTES_PER_CHANNEL = 3
_BYTES_PER_SAMPLE = 2 * _BYTES_PER_CHANNEL
# smbus2.SMBus.read_i2c_block_data бросает ValueError при length > 32. Читаем
# кусками по 30 байт (5 отсчётов): кратно 6, отсчёт не рвётся между кусками.
_MAX_SAMPLES_PER_READ = 5
_SAMPLE_VALUE_MASK = 0x03FFFF


class Max30102:
    def __init__(self, bus: Any, addr: int, *, led_pa: int = 0x23) -> None:
        if not 0 <= led_pa <= 0xFF:
            raise ValueError("led_pa должен быть 0..255, получено %r" % (led_pa,))
        self._bus = bus
        self._addr = addr
        self._led_pa = led_pa

    def part_id(self) -> int:
        return self._bus.read_byte_data(self._addr, _REG_PART_ID)

    def initialize(self) -> None:
        """Сброс и настройка чипа на режим SpO2, 50 отсчётов/с, 18 бит.

        После включения питания все регистры конфигурации равны 0x00: MODE = 000
        ("Do not use", Table 4), токи светодиодов 0 мА (Table 8) — без настройки
        чип ничего не измеряет. Порядок:
        1. RESET (бит 6 MODE_CONFIG) и ожидание, пока чип его сбросит;
        2. FIFO_CONFIG, SPO2_CONFIG, токи LED1_PA / LED2_PA;
        3. обнуление FIFO_WR_PTR, OVF_COUNTER, FIFO_RD_PTR — даташит рекомендует
           это перед началом измерений (стр. 14–15);
        4. MODE = SpO2 (011), SHDN = 0 — измерения начинаются.

        Если чип так и не сбросил RESET, бросается `OSError(ETIMEDOUT)`: для
        `Sampler` это "датчик не отвечает", как и обрыв шины.
        """
        self._bus.write_byte_data(self._addr, _REG_MODE_CONFIG, _RESET_BIT)
        for _ in range(_RESET_POLL_ATTEMPTS):
            if not self._bus.read_byte_data(self._addr, _REG_MODE_CONFIG) & _RESET_BIT:
                break
        else:
            raise OSError(errno.ETIMEDOUT, "MAX30102 не завершил сброс (бит RESET)")
        self._bus.write_byte_data(self._addr, _REG_FIFO_CONFIG, _FIFO_CONFIG_VALUE)
        self._bus.write_byte_data(self._addr, _REG_SPO2_CONFIG, _SPO2_CONFIG_VALUE)
        self._bus.write_byte_data(self._addr, _REG_LED1_PA, self._led_pa)
        self._bus.write_byte_data(self._addr, _REG_LED2_PA, self._led_pa)
        for reg in (_REG_FIFO_WR_PTR, _REG_OVF_COUNTER, _REG_FIFO_RD_PTR):
            self._bus.write_byte_data(self._addr, reg, 0x00)
        self._bus.write_byte_data(self._addr, _REG_MODE_CONFIG, _MODE_SPO2)

    def read_fifo_samples(self, count: int) -> list[tuple[int, int]]:
        """Читает ровно `count` отсчётов `(red, ir)` блочными чтениями.

        Не более 5 отсчётов (30 байт) за транзакцию — лимит smbus2 в 32 байта.
        Драйвер не знает, сколько отсчётов реально есть: сначала вызывайте
        `available_samples()`. При пустом FIFO вернутся пары (0, 0).

        Число доступных отсчётов не определяется: разница FIFO_WR_PTR и
        FIFO_RD_PTR (5 бит, mod 32) не отличает пустую очередь от полной
        (неоднозначность и у настоящего чипа: даташит, стр. 16, лишь просит
        учитывать оборот указателей).
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
        Здесь это не разрешается; признак полного FIFO — `overflow_count() > 0`
        (при выключенном rollover следующий отсчёт теряется и счётчик растёт).
        """
        block = self._bus.read_i2c_block_data(self._addr, _REG_FIFO_WR_PTR, 3)
        return (block[0] - block[2]) % _FIFO_DEPTH

    def overflow_count(self) -> int:
        return self._bus.read_byte_data(self._addr, _REG_OVF_COUNTER)

    @staticmethod
    def _channel(data: list[int], offset: int) -> int:
        value = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2]
        return value & _SAMPLE_VALUE_MASK
