"""`VirtualMPU6050` — виртуальный чип акселерометра MPU6050 (PI-02): реализует
протокол `RegisterDevice` (`device/bus/fake_smbus.py`) и моделирует только
регистры, нужные акселерометру — `WHO_AM_I`, `PWR_MGMT_1` (сон),
`ACCEL_CONFIG` (диапазон), `ACCEL_XOUT_H..ACCEL_ZOUT_L` (данные). Гироскоп,
температура, FIFO, прерывания — вне скоупа (не нужны ни одной текущей
задаче, `docs/pi.md` §6 перечисляет только то, что нужно моделировать).

Данные берутся из произвольного `Iterator[tuple[x, y, z]]` (в g), который
передаёт вызывающий код — например `accel_samples()` из
`device/virtual/signals.py` (PI-04) или тестовый фейк. Этот модуль
намеренно не импортирует `device.virtual.signals`/`scenarios` (см. границы
задачи PI-02): какой источник подключить — решение потребителя
(тестов здесь, драйвера MPU6050 позже в PI-05/PI-08).

Источники данных по даташиту — "MPU-6000 and MPU-6050 Register Map and
Descriptions", Revision 4.2, InvenSense:
https://www.invensense.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf
(зеркало: https://shop.cpu.com.tw/upload/2013/03/RM-MPU-6000A.pdf).
Независимое подтверждение тех же LSB/g и битов диапазона — драйвер ядра
Linux `inv_mpu6050`:
https://elixir.free-electrons.com/linux/v5.3.7/source/drivers/iio/imu/inv_mpu6050/inv_mpu_core.c
(вторичный источник, не основной).
"""

from __future__ import annotations

from collections.abc import Iterator

# --- Регистры (датащит InvenSense, см. docstring модуля) --------------------

_REG_ACCEL_CONFIG = 0x1C
_REG_PWR_MGMT_1 = 0x6B
_REG_WHO_AM_I = 0x75
_REG_ACCEL_XOUT_H = 0x3B
_REG_ACCEL_ZOUT_L = 0x40  # ACCEL_XOUT_H..ACCEL_ZOUT_L = 6 последовательных байт

# WHO_AM_I всегда возвращает 0x68 независимо от реального адреса устройства
# на шине (бит AD0 на выбор адреса не влияет, но не влияет и на это
# значение) — датащит, регистр 0x75.
_WHO_AM_I_VALUE = 0x68

# PWR_MGMT_1: значение регистра при включении питания = 0x40, т.е. бит 6
# (SLEEP) установлен в 1 по умолчанию — датащит, регистр 0x6B.
_PWR_MGMT_1_RESET = 0x40
_SLEEP_BIT = 0x40  # бит 6

# ACCEL_CONFIG, биты 4:3 = AFS_SEL — датащит, регистр 0x1C.
_AFS_SEL_MASK = 0b0001_1000
_AFS_SEL_SHIFT = 3

# LSB/g для каждого значения AFS_SEL — датащит (см. docstring модуля):
# 0 = ±2g (16384 LSB/g), 1 = ±4g (8192), 2 = ±8g (4096), 3 = ±16g (2048).
_LSB_PER_G: dict[int, int] = {
    0: 16384,
    1: 8192,
    2: 4096,
    3: 2048,
}

_INT16_MIN = -32768
_INT16_MAX = 32767

_ZERO_SAMPLE = (0.0, 0.0, 0.0)
_SLEEP_ACCEL_BYTES = [0, 0, 0, 0, 0, 0]


class VirtualMPU6050:
    """Виртуальный MPU6050 на шине `FakeSMBus` (PI-01), только акселерометр.

    `source` — произвольный итератор отсчётов `(x, y, z)` в g; у чипа нет
    собственной зависимости от того, как эти отсчёты сгенерированы (своё
    решение задачи PI-02, см. Boundaries & Constraints спеки).
    """

    def __init__(
        self,
        source: Iterator[tuple[float, float, float]],
        *,
        who_am_i: int = _WHO_AM_I_VALUE,
    ) -> None:
        self._source = source
        self._who_am_i = who_am_i

        # После создания чип "спит" — датащит, PWR_MGMT_1 reset = 0x40.
        self._pwr_mgmt_1 = _PWR_MGMT_1_RESET
        # ACCEL_CONFIG reset = 0x00 => AFS_SEL = 0 => ±2g — датащит.
        self._accel_config = 0x00

        # Последний полученный от источника отсчёт (в g) — используется для
        # повтора при исчерпании источника (own decision, см. docstring
        # модуля и Boundaries & Constraints: "не ошибка, повторяется
        # последний отсчёт").
        self._last_sample: tuple[float, float, float] = _ZERO_SAMPLE

        # Кэш 6 байт текущего "логического чтения" ACCEL_XOUT_H..ZOUT_L —
        # обновляется только когда доступ происходит именно к ACCEL_XOUT_H
        # (первому байту блока), чтобы побайтовое чтение не перемешивало
        # оси из разных отсчётов (own decision, см. Design Notes спеки).
        # Чип только что создан и спит, поэтому исходно это нулевой блок —
        # совпадает с тем, что выдал бы _refresh_accel_cache() в состоянии сна.
        self._accel_cache: list[int] = list(_SLEEP_ACCEL_BYTES)

    @property
    def _sleeping(self) -> bool:
        return bool(self._pwr_mgmt_1 & _SLEEP_BIT)

    @property
    def _range_code(self) -> int:
        return (self._accel_config & _AFS_SEL_MASK) >> _AFS_SEL_SHIFT

    # --- RegisterDevice -------------------------------------------------

    def write_byte_data(self, reg: int, val: int) -> None:
        val &= 0xFF
        if reg == _REG_PWR_MGMT_1:
            self._pwr_mgmt_1 = val
        elif reg == _REG_ACCEL_CONFIG:
            self._accel_config = val
        # Немоделируемый регистр: запись принимается и игнорируется — own
        # decision, см. Boundaries & Constraints спеки ("чип моделирует
        # только регистры, нужные для шагов").

    def read_byte_data(self, reg: int) -> int:
        if reg == _REG_WHO_AM_I:
            return self._who_am_i
        if reg == _REG_PWR_MGMT_1:
            return self._pwr_mgmt_1
        if reg == _REG_ACCEL_CONFIG:
            return self._accel_config
        if _REG_ACCEL_XOUT_H <= reg <= _REG_ACCEL_ZOUT_L:
            return self._accel_byte(reg - _REG_ACCEL_XOUT_H)
        # Немоделируемый регистр: читается как 0 — own decision (см. выше).
        return 0

    def read_i2c_block_data(self, reg: int, length: int) -> list[int]:
        if _REG_ACCEL_XOUT_H <= reg <= _REG_ACCEL_ZOUT_L:
            start_offset = reg - _REG_ACCEL_XOUT_H
            return [self._accel_byte(start_offset + i) for i in range(length)]
        # Немоделируемый диапазон регистров поблочно: тот же контракт
        # "неизвестный регистр -> 0" применяется байт за байтом.
        return [self.read_byte_data(reg + i) for i in range(length)]

    # --- внутреннее состояние -------------------------------------------

    def _accel_byte(self, offset: int) -> int:
        """Байт `offset` (0..5) блока ACCEL_XOUT_H..ACCEL_ZOUT_L.

        `offset == 0` соответствует ACCEL_XOUT_H — первому байту блока,
        доступ к которому запускает новое "логическое чтение" (новый
        отсчёт из источника). Остальные смещения отдаются из уже
        посчитанного на этом логическом чтении кэша.

        `offset` вне `0..5` означает, что блочное чтение (`read_i2c_block_data`)
        вышло за пределы 6-байтового accel-блока в немоделируемые регистры —
        тот же контракт "неизвестный регистр -> 0", own decision, что и для
        одиночного `read_byte_data` немоделируемого регистра.
        """
        if offset == 0:
            self._refresh_accel_cache()
        if not 0 <= offset < len(self._accel_cache):
            return 0
        return self._accel_cache[offset]

    def _refresh_accel_cache(self) -> None:
        if self._sleeping:
            # Во сне АЦП не производит новых отсчётов — датащит описывает
            # только то, что данные во сне недоступны (docs/pi.md §6:
            # "недоступное при сне чипа"); то, что источник при этом не
            # потребляется, — own decision этой задачи, выбранное как самое
            # простое поведение, не противоречащее ни даташиту, ни спеке.
            self._accel_cache = list(_SLEEP_ACCEL_BYTES)
            return

        self._last_sample = self._pull_next_sample()
        self._accel_cache = self._encode_sample(self._last_sample, self._range_code)

    def _pull_next_sample(self) -> tuple[float, float, float]:
        try:
            return next(self._source)
        except StopIteration:
            # Источник исчерпан — не ошибка: повторяем последний полученный
            # отсчёт (own decision, Boundaries & Constraints спеки).
            return self._last_sample

    @staticmethod
    def _encode_sample(
        sample: tuple[float, float, float], range_code: int
    ) -> list[int]:
        """Кодирует `(x, y, z)` в g в 6 байт big-endian int16 для текущего
        диапазона: `raw = round(value_g * LSB/g)`, с насыщением на границах
        int16 — на реальном чипе физическое насыщение выглядит так же
        (значение "прижимается" к пределу, а не оборачивается), Design
        Notes спеки.
        """
        lsb_per_g = _LSB_PER_G[range_code]
        raw_bytes: list[int] = []
        for value_g in sample:
            raw = round(value_g * lsb_per_g)
            raw = max(_INT16_MIN, min(_INT16_MAX, raw))
            unsigned = raw & 0xFFFF
            raw_bytes.append((unsigned >> 8) & 0xFF)  # *_H, старший байт первым
            raw_bytes.append(unsigned & 0xFF)  # *_L
        return raw_bytes
