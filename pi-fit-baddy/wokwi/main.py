"""Pi Pico в Wokwi: наш драйвер MPU6050 против симулированного датчика.

Файлы проекта Wokwi: main.py, checks.py, mpu6050.py (= device/drivers/mpu6050.py), diagram.json.
"""

import time

from machine import I2C, Pin

from checks import run_checks, stream
from mpu6050 import Mpu6050

ADDR = 0x68
STREAM_SECONDS = 60
STREAM_HZ = 50


class SMBusI2C:
    """Те же три метода, что у smbus2.SMBus, поверх machine.I2C — драйвер не меняется."""

    def __init__(self, i2c):
        self._i2c = i2c

    def read_byte_data(self, addr, reg):
        return self._i2c.readfrom_mem(addr, reg, 1)[0]

    def write_byte_data(self, addr, reg, val):
        self._i2c.writeto_mem(addr, reg, bytes([val & 0xFF]))

    def read_i2c_block_data(self, addr, reg, length):
        return list(self._i2c.readfrom_mem(addr, reg, length))


i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
print("I2C scan:", [hex(a) for a in i2c.scan()])
bus = SMBusI2C(i2c)

run_checks(bus, ADDR, print)

print("STREAM %d s at %d Hz: двигайте ползунок accelZ датчика вверх-вниз, считая шаги" % (STREAM_SECONDS, STREAM_HZ))
stream(Mpu6050(bus, ADDR), STREAM_SECONDS, STREAM_HZ,
       lambda: time.ticks_ms() / 1000.0, time.sleep, print)
