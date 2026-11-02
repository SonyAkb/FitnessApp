"""Драйвер акселерометра MPU6050 (PI-05).

Шина и адрес приходят через конструктор. Используются только
`write_byte_data(addr, reg, val)`, `read_byte_data(addr, reg)` и
`read_i2c_block_data(addr, reg, length)` — методы, общие для `smbus2.SMBus` и
`FakeSMBus` (docs/pi.md §3 правило 2). Проверок режима mock/real здесь нет.
Файл без `__future__` и `typing`: он же запускается на Pi Pico под MicroPython
в симуляторе Wokwi (`wokwi/`) для сверки с независимой моделью MPU6050.

Регистры и LSB/g — "MPU-6000 and MPU-6050 Register Map and Descriptions",
Revision 4.2, InvenSense:
https://www.invensense.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf
Таблица LSB/g — собственная копия драйвера (на настоящем чипе это константа из
даташита, а не данные виртуального чипа PI-02).
"""

_REG_ACCEL_CONFIG = 0x1C
_REG_ACCEL_XOUT_H = 0x3B
_REG_PWR_MGMT_1 = 0x6B
_REG_WHO_AM_I = 0x75

_SLEEP_BIT = 0x40  # PWR_MGMT_1, бит 6
_AFS_SEL_MASK = 0b0001_1000  # ACCEL_CONFIG, биты 4:3
_AFS_SEL_SHIFT = 3

# 0 = ±2g, 1 = ±4g, 2 = ±8g, 3 = ±16g (датащит InvenSense, см. docstring).
_LSB_PER_G: dict[int, int] = {0: 16384, 1: 8192, 2: 4096, 3: 2048}

_ACCEL_BLOCK_LEN = 6


class Mpu6050:
    def __init__(self, bus: object, addr: int) -> None:
        self._bus = bus
        self._addr = addr
        # Диапазон неизвестен до set_range() или первого чтения: на реальной
        # плате чип мог остаться настроенным с прошлого запуска. Ввода-вывода
        # в конструкторе нет.
        self._range_code: int | None = None

    def who_am_i(self) -> int:
        return self._bus.read_byte_data(self._addr, _REG_WHO_AM_I)

    def wake(self) -> None:
        """Сбрасывает бит SLEEP, сохраняя остальные биты PWR_MGMT_1."""
        value = self._bus.read_byte_data(self._addr, _REG_PWR_MGMT_1)
        self._bus.write_byte_data(self._addr, _REG_PWR_MGMT_1, value & ~_SLEEP_BIT & 0xFF)

    def set_range(self, range_code: int) -> None:
        """Пишет AFS_SEL (биты 4:3 ACCEL_CONFIG), остальные биты сохраняются."""
        if range_code not in _LSB_PER_G:
            raise ValueError("range_code должен быть 0..3, получено %r" % (range_code,))
        value = self._bus.read_byte_data(self._addr, _REG_ACCEL_CONFIG)
        value = (value & ~_AFS_SEL_MASK & 0xFF) | (range_code << _AFS_SEL_SHIFT)
        self._bus.write_byte_data(self._addr, _REG_ACCEL_CONFIG, value)
        self._range_code = range_code

    def read_acceleration_g(self) -> tuple[float, float, float]:
        """Одно показание (x, y, z) в g.

        Блок читается ОДНИМ вызовом (иначе оси могут "порваться" между
        отсчётами, см. PI-02). Драйвер сам чип не будит: спящий чип отдаёт нули.
        """
        block = self._bus.read_i2c_block_data(
            self._addr, _REG_ACCEL_XOUT_H, _ACCEL_BLOCK_LEN
        )
        if self._range_code is None:
            config = self._bus.read_byte_data(self._addr, _REG_ACCEL_CONFIG)
            self._range_code = (config & _AFS_SEL_MASK) >> _AFS_SEL_SHIFT
        lsb_per_g = _LSB_PER_G[self._range_code]
        axes: list[float] = []
        for i in range(0, _ACCEL_BLOCK_LEN, 2):
            raw = (block[i] << 8) | block[i + 1]
            if raw >= 0x8000:
                raw -= 0x10000
            axes.append(raw / lsb_per_g)
        return (axes[0], axes[1], axes[2])
