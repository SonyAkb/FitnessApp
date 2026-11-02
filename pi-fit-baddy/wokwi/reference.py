"""Те же проверки `checks.py` на нашей модели: FakeSMBus + VirtualMPU6050 (CPython).

    python -m wokwi.reference        # из pi-fit-baddy/

Вывод сравнивают строка в строку с выводом Pi Pico в Wokwi (accelZ = 1 g, остальные оси 0).
"""

import itertools
import os
import sys

# checks.py импортирует драйвер как `mpu6050` — так он лежит и в проекте Wokwi.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "device", "drivers"))

from device.bus.fake_smbus import FakeSMBus  # noqa: E402
from device.virtual.mpu6050 import VirtualMPU6050  # noqa: E402
from wokwi.checks import run_checks  # noqa: E402

ADDR = 0x68


def main(log=print) -> tuple[int, int]:
    bus = FakeSMBus()
    bus.register_device(ADDR, VirtualMPU6050(itertools.repeat((0.0, 0.0, 1.0))))
    log("I2C scan: ['0x68']")
    return run_checks(bus, ADDR, log)


if __name__ == "__main__":
    passed, total = main()
    sys.exit(0 if passed == total else 1)
