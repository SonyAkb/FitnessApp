"""Проверки MPU6050 — один файл для Pi Pico в Wokwi (MicroPython) и для нашей модели (CPython).

Каждая строка `CHECK` сравнивает поведение чипа с даташитом InvenSense (Register Map rev 4.2):
WHO_AM_I = 0x68, после включения PWR_MGMT_1 = 0x40 (сон, данные — нули), ±2g = 16384 LSB/g,
±8g = 4096 LSB/g. Драйвер — тот же файл `device/drivers/mpu6050.py`, что работает на узле.
Без `__future__`, `typing` и f-строк с форматированием — чтобы работало в MicroPython.
"""

from mpu6050 import Mpu6050

REG_ACCEL_XOUT_H = 0x3B
REG_PWR_MGMT_1 = 0x6B


def raw_axes(bus, addr):
    """Сырые значения осей (signed 16 bit, big-endian) одним блочным чтением."""
    block = bus.read_i2c_block_data(addr, REG_ACCEL_XOUT_H, 6)
    axes = []
    for i in range(0, 6, 2):
        value = (block[i] << 8) | block[i + 1]
        if value >= 0x8000:
            value -= 0x10000
        axes.append(value)
    return axes


def run_checks(bus, addr, log):
    """Возвращает (пройдено, всего). Ожидания — по даташиту, а не по нашей модели."""
    results = []

    def check(name, got, expected, note):
        ok = got == expected
        results.append(ok)
        log("CHECK %-28s %s  got=%s expected=%s  (%s)" % (name, "OK  " if ok else "DIFF", got, expected, note))

    driver = Mpu6050(bus, addr)
    check("who_am_i", hex(driver.who_am_i()), "0x68", "регистр 0x75")
    check("pwr_mgmt_1_on_power_up", hex(bus.read_byte_data(addr, REG_PWR_MGMT_1)), "0x40", "бит SLEEP после включения")
    check("accel_while_asleep", raw_axes(bus, addr), [0, 0, 0], "спящий чип отдаёт нули")

    driver.wake()
    check("pwr_mgmt_1_after_wake", hex(bus.read_byte_data(addr, REG_PWR_MGMT_1)), "0x0", "драйвер сбросил SLEEP")

    driver.set_range(0)
    raw_2g = raw_axes(bus, addr)
    g_2g = driver.read_acceleration_g()
    log("DATA  range=±2g raw=%s g=(%.3f, %.3f, %.3f)" % (raw_2g, g_2g[0], g_2g[1], g_2g[2]))

    driver.set_range(2)
    raw_8g = raw_axes(bus, addr)
    g_8g = driver.read_acceleration_g()
    log("DATA  range=±8g raw=%s g=(%.3f, %.3f, %.3f)" % (raw_8g, g_8g[0], g_8g[1], g_8g[2]))
    driver.set_range(0)

    if raw_2g[2] == 0:
        log("SKIP  range checks: ось Z = 0 — поставьте accelZ = 1 g и перезапустите")
    else:
        check("raw_z_ratio_8g_to_2g", round(raw_8g[2] / raw_2g[2], 2), 0.25, "4096 / 16384 LSB/g")
        check("driver_g_same_on_both", abs(g_8g[2] - g_2g[2]) < 0.05, True, "драйвер учитывает диапазон")

    passed = sum(1 for ok in results if ok)
    log("RESULT %d/%d checks match the datasheet" % (passed, len(results)))
    return passed, len(results)


def stream(driver, seconds, rate_hz, now_s, sleep_s, log):
    """Печатает отсчёты в формате CSV-проигрывателя узла (`t,x,y,z`, t — секунды от начала)."""
    log("CSV-BEGIN t,x,y,z")
    start = now_s()
    period = 1.0 / rate_hz
    next_at = start
    while now_s() - start < seconds:
        x, y, z = driver.read_acceleration_g()
        log("%.3f,%.4f,%.4f,%.4f" % (now_s() - start, x, y, z))
        next_at += period
        delay = next_at - now_s()
        if delay > 0:
            sleep_s(delay)
    log("CSV-END")
