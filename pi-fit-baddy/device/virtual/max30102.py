"""`VirtualMax30102` — виртуальный чип пульсоксиметра MAX30102 (PI-03):
реализует протокол `RegisterDevice` (`device/bus/fake_smbus.py`) и моделирует
собственный циклический FIFO на 32 отсчёта, указатели `FIFO_WR_PTR`/
`FIFO_RD_PTR`, 4-битный `OVF_COUNTER`, `PART_ID` и минимальную поддержку
`MODE_CONFIG` (бит `SHDN`). SpO2-масштабирование АЦП, усреднение по
`SMP_AVE`, `FIFO_ROLLOVER_EN` — вне скоупа (не нужны ни DoD, ни текущим
потребителям).

Данные берутся из произвольного `Iterator[tuple[ir, red]]` (сырые единицы,
без масштабирования), который передаёт вызывающий код — например
`ppg_samples()` из `device/virtual/signals.py` (PI-04) или тестовый фейк.
Этот модуль намеренно не импортирует `device.virtual.scenarios`/`signals`
(тот же приём декомпозиции, что и в PI-02): какой источник подключить — решение потребителя.

Источники данных по даташиту — официальный даташит Analog Devices (бывший
Maxim) MAX30102:
https://wcm-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf
— основной источник для структуры регистров и таблицы частот SPO2_SR.
MAX30102 заметно менее документирован в открытых источниках, чем MPU6050 —
там, где уверенность ниже, это явно обозначено ниже у конкретных констант.
"""

from __future__ import annotations

from collections.abc import Iterator

# --- Регистры (docs/pi.md §4, таблица MAX30102 0x00-0x0D, 0xFE/0xFF) --------

_REG_INT_STATUS = 0x00
_REG_INT_ENABLE = 0x02
_REG_FIFO_WR_PTR = 0x04
_REG_OVF_COUNTER = 0x05
_REG_FIFO_RD_PTR = 0x06
_REG_FIFO_DATA = 0x07
_REG_FIFO_CONFIG = 0x08
_REG_MODE_CONFIG = 0x09
_REG_LED1_PA = 0x0C
_REG_LED2_PA = 0x0D
_REG_REV_ID = 0xFE
_REG_PART_ID = 0xFF

# PART_ID = 0x15 — подтверждено согласованно в нескольких независимых
# открытых реализациях драйверов MAX30102/MAX30105 (не прямая цитата из
# PDF даташита).
_PART_ID_VALUE = 0x15

# Глубина FIFO и ширина указателей — согласованно по даташиту и множеству
# независимых открытых реализаций.
_FIFO_DEPTH = 32
_PTR_MASK = 0x1F  # 5 бит, оборот по модулю 32

# OVF_COUNTER — 4-битный счётчик, насыщается на максимуме (не оборачивается
# через 0) — согласованно по даташиту и множеству независимых реализаций.
_OVF_COUNTER_MAX = 15

# MODE_CONFIG бит 7 = SHDN (own decision: дефолт при создании = 0, чип не
# выключен — не подтверждено даташитом напрямую в рамках этой задачи).
# TODO(datasheet): сверить дефолтное
# значение MODE_CONFIG при включении питания по тексту даташита.
_SHDN_BIT = 0x80
_MODE_CONFIG_RESET = 0x00

# Формат отсчёта FIFO: 3 байта на канал, порядок RED, затем IR — own
# decision/провизорно, подтверждено согласованностью нескольких независимых
# реализаций драйверов, но не прямой цитатой из PDF. TODO(datasheet):
# сверить порядок RED/IR байт по тексту даташита (раздел FIFO Data
# Register) при проверке на реальной плате в PI-10.
_BYTES_PER_CHANNEL = 3
_BYTES_PER_SAMPLE = 2 * _BYTES_PER_CHANNEL
_SAMPLE_VALUE_MASK = 0x03FFFF  # 18 бит значимых, старшие 6 бит контейнера — 0


class VirtualMax30102:
    """Виртуальный MAX30102 на шине `FakeSMBus` (PI-01), только FIFO/PART_ID.

    `source` — произвольный итератор отсчётов `(ir, red)` в сырых единицах
    (без масштабирования); у чипа нет собственной зависимости от того, как
    эти отсчёты сгенерированы (own decision задачи PI-03, тот же приём, что
    и в PI-02).

    Пополнение FIFO триггерится чтением `FIFO_WR_PTR` — own decision,
    замена "по часам" (`docs/pi.md §6`) на "по логическому чтению", тот же
    приём декомпозиции, что уже прошёл ревью в PI-02: у чипа нет собственной зависимости от `Clock`.

    Ограничение для будущих потребителей (важно для драйвера PI-05): прямая
    запись `write_byte_data` в `FIFO_WR_PTR`/`FIFO_RD_PTR` устанавливает
    только значение указателя (без побочных
    эффектов) и НЕ синхронизирует внутренний счётчик занятых слотов FIFO
    (`_fifo_slots_used`) и содержимое буфера. Такая прямая запись мимо
    обычного цикла "читать FIFO_WR_PTR → пополнение" / "читать FIFO_DATA →
    вычитывание" разводит указатели с фактическим состоянием очереди —
    ни один текущий тест/потребитель так не делает, но будущий код не
    должен на это полагаться.
    """

    def __init__(self, source: Iterator[tuple[int, int]]) -> None:
        self._source = source

        self._wr_ptr = 0
        self._rd_ptr = 0
        self._ovf_counter = 0
        self._mode_config = _MODE_CONFIG_RESET

        # Циклический буфер неприведённых отсчётов (red, ir) — хранит ровно
        # то, что лежит "между" RD_PTR и WR_PTR; слоты вне этого диапазона
        # не имеют смысла (как и в реальном FIFO, где непрочитанное
        # содержимое ячейки не определено до следующей записи).
        self._fifo: list[tuple[int, int]] = [(0, 0)] * _FIFO_DEPTH

        # Число непрочитанных отсчётов в очереди (0..32) — отдельный
        # счётчик, а не разница WR_PTR-RD_PTR: при полной очереди ровно
        # 32 отсчёта оба указателя совпадают (WR_PTR обошёл круг и
        # вернулся к RD_PTR), а RD_PTR == WR_PTR означает именно
        # "пусто" для FIFO_DATA — own decision, нужное, чтобы отличать
        # "пусто" от "полно" без двух разных толкований одного сравнения
        # указателей.
        self._fifo_slots_used = 0

        # Счётчик байт (0..5) уже отданных из текущего "самого старого"
        # отсчёта при последовательных чтениях FIFO_DATA — own decision,
        # тот же приём "кэш текущего логического чтения", что в PI-02.
        self._fifo_data_byte_offset = 0

    @property
    def _shdn(self) -> bool:
        return bool(self._mode_config & _SHDN_BIT)

    # --- RegisterDevice ---------------------------------------------------

    def write_byte_data(self, reg: int, val: int) -> None:
        val &= 0xFF
        if reg == _REG_FIFO_WR_PTR:
            self._wr_ptr = val & _PTR_MASK
        elif reg == _REG_FIFO_RD_PTR:
            # Запись устанавливает значение указателя напрямую, без
            # побочных эффектов — счётчик байт текущего
            # отсчёта и число занятых слотов этим не трогаются; это же
            # значит, что прямая запись RD_PTR/WR_PTR мимо чтения
            # FIFO_WR_PTR/FIFO_DATA может развести эти два счётчика с
            # фактическими указателями — вне скоупа текущих потребителей
            # и тестов (own decision).
            self._rd_ptr = val & _PTR_MASK
        elif reg == _REG_OVF_COUNTER:
            self._ovf_counter = val & 0x0F
        elif reg == _REG_MODE_CONFIG:
            self._mode_config = val
        # Немоделируемый регистр (INT_STATUS, INT_ENABLE, FIFO_CONFIG,
        # LED1_PA, LED2_PA, REV_ID): запись принимается и игнорируется —
        # own decision, тот же паттерн, что и в PI-02.

    def read_byte_data(self, reg: int) -> int:
        if reg == _REG_PART_ID:
            return _PART_ID_VALUE
        if reg == _REG_FIFO_WR_PTR:
            # Возвращается значение указателя ДО попытки пополнения этим же
            # чтением (own decision: без этого самый первый вызов на свежем
            # чипе вернул бы 1, а не 0, что нарушает требование
            # "только что созданный чип, читаются WR_PTR/
            # RD_PTR/OVF_COUNTER -> все равны 0"). Пополнение всё равно
            # происходит при каждом чтении -- эффект виден на СЛЕДУЮЩЕМ
            # чтении WR_PTR/FIFO_DATA.
            current = self._wr_ptr
            self._maybe_enqueue()
            return current
        if reg == _REG_FIFO_RD_PTR:
            return self._rd_ptr
        if reg == _REG_OVF_COUNTER:
            return self._ovf_counter
        if reg == _REG_MODE_CONFIG:
            return self._mode_config
        if reg == _REG_FIFO_DATA:
            return self._read_fifo_data_byte()
        # Немоделируемый регистр (INT_STATUS, INT_ENABLE, FIFO_CONFIG,
        # LED1_PA, LED2_PA, REV_ID): читается как 0 — own decision, тот же
        # паттерн, что и в PI-02.
        return 0

    def read_i2c_block_data(self, reg: int, length: int) -> list[int]:
        if reg == _REG_FIFO_DATA:
            # FIFO_DATA — порт вычитывания, не авто-инкрементирующийся
            # регистр: на реальном чипе каждая транзакция читает тот же
            # адрес и получает очередной байт текущего отсчёта (own
            # decision/datasheet-convention для FIFO-портов). Повторный
            # вызов read_byte_data(reg) с тем же reg корректно воспроизводит
            # это — внутренний байт-обход уже учитывается _read_fifo_data_byte.
            return [self.read_byte_data(reg) for _ in range(length)]
        # Любой другой регистр — обычный блок из `length` ПОСЛЕДОВАТЕЛЬНЫХ
        # адресов (reg, reg+1, ...), тот же контракт, что у read_i2c_block_data
        # в PI-02 (VirtualMPU6050): так блок из нескольких статусных
        # регистров (например FIFO_WR_PTR/OVF_COUNTER/FIFO_RD_PTR — они
        # идут подряд, 0x04-0x06) читается в одной транзакции корректно,
        # а не как `length` повторов одного и того же регистра.
        return [self.read_byte_data(reg + i) for i in range(length)]

    # --- внутреннее состояние ---------------------------------------------

    def _maybe_enqueue(self) -> None:
        """Пытается пополнить FIFO одним отсчётом источника — вызывается при
        чтении `FIFO_WR_PTR` (own decision, см. docstring класса).
        """
        if self._shdn:
            # Пока чип "выключен" (SHDN=1), пополнение не происходит —
            # тот же общий принцип "недоступное при сне чипа" (docs/pi.md
            # §6), что и в PI-02 (там — PWR_MGMT_1/SLEEP).
            return

        if self._fifo_slots_used >= _FIFO_DEPTH:
            # Очередь уже содержит 32 непрочитанных отсчёта — новый
            # отсчёт отбрасывается, WR_PTR не продвигается, OVF_COUNTER
            # растёт с насыщением на 15 (docs/pi.md §6: "при невычитанном
            # FIFO растёт OVF_COUNTER").
            self._ovf_counter = min(_OVF_COUNTER_MAX, self._ovf_counter + 1)
            return

        try:
            ir, red = next(self._source)
        except StopIteration:
            # Источник исчерпан — не ошибка: в отличие от PI-02 (где есть
            # один "текущий" отсчёт, естественно повторяемый), здесь нет
            # отдельного текущего отсчёта вне очереди, который было бы
            # разумно повторять, поэтому пополнение в этот раз просто не
            # происходит — очередь остаётся как была, без отброшенного
            # отсчёта и без роста OVF_COUNTER (own decision).
            return

        self._fifo[self._wr_ptr] = (red, ir)
        self._wr_ptr = (self._wr_ptr + 1) & _PTR_MASK
        self._fifo_slots_used += 1

    def _read_fifo_data_byte(self) -> int:
        if self._fifo_slots_used == 0:
            # Пустая очередь (RD_PTR == WR_PTR) -> 0 на любой байт — own
            # decision, тот же паттерн "нет данных -> 0", что у PI-02.
            return 0

        red, ir = self._fifo[self._rd_ptr]
        channel_bytes = self._encode_sample(red, ir)
        byte_value = channel_bytes[self._fifo_data_byte_offset]

        self._fifo_data_byte_offset += 1
        if self._fifo_data_byte_offset >= _BYTES_PER_SAMPLE:
            # 6-й байт отдан — переход к следующему отсчёту: RD_PTR
            # продвигается на 1 (mod 32), слот освобождён.
            self._fifo_data_byte_offset = 0
            self._rd_ptr = (self._rd_ptr + 1) & _PTR_MASK
            self._fifo_slots_used -= 1

        return byte_value

    @staticmethod
    def _encode_sample(red: int, ir: int) -> list[int]:
        """Кодирует один отсчёт `(red, ir)` в 6 байт: 3 байта RED, затем
        3 байта IR, big-endian, 18 бит значимых (старшие 6 бит контейнера
        всегда 0) — провизорное решение (порядок каналов), см. TODO(datasheet) выше.
        """
        result: list[int] = []
        for value in (red, ir):
            masked = value & _SAMPLE_VALUE_MASK
            result.append((masked >> 16) & 0xFF)
            result.append((masked >> 8) & 0xFF)
            result.append(masked & 0xFF)
        return result
