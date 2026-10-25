"""Проект Wokwi (`wokwi/`): проверки драйвера MPU6050 и подсчёт шагов по потоку из симулятора."""

import os
import shutil
import subprocess

import pytest

from wokwi import count_steps, reference

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_our_virtual_chip_passes_the_same_checks_as_wokwi():
    lines = []
    passed, total = reference.main(lines.append)
    assert (passed, total) == (6, 6), "\n".join(lines)


def _walk(steps, rate_hz=50, step_s=0.6):
    """Поток, как при движении ползунка accelZ: покой, затем на каждый шаг пик 1.5 g и возврат к 1 g."""
    lines, t = ["CSV-BEGIN t,x,y,z"], 0.0
    for _ in range(int(0.5 * rate_hz)):  # поток начинается с покоя: пик засчитывается по нарастанию
        lines.append("%.3f,0.0,0.0,1.000" % t)
        t += 1.0 / rate_hz
    for _ in range(steps):
        for i in range(int(step_s * rate_hz)):
            z = 1.5 if i < int(0.15 * rate_hz) else 1.0
            lines.append("%.3f,0.0,0.0,%.3f" % (t, z))
            t += 1.0 / rate_hz
    lines.append("CSV-END")
    return lines


def test_stream_from_wokwi_log_is_parsed_and_counted(monkeypatch):
    for name in ("STEP_THRESHOLD_G", "STEP_MIN_INTERVAL_MS", "STEP_SMOOTHING_SAMPLES"):
        monkeypatch.delenv(name, raising=False)
    log = ["I2C scan: ['0x68']", "RESULT 6/6"] + _walk(10) + ["MicroPython REPL >>>"]
    samples = count_steps.parse_stream(log)
    assert len(samples) == 25 + 10 * 30
    assert count_steps.count(samples) == 10


def test_count_steps_cli_saves_csv_for_the_player(tmp_path, capsys):
    log = tmp_path / "log.txt"
    log.write_text("\n".join(_walk(4)), encoding="utf-8")
    assert count_steps.main([str(log), "--save", str(tmp_path / "walk")]) == 0
    assert "Шагов по нашему алгоритму: 4" in capsys.readouterr().out
    from device.virtual.csv_player import accel_samples_from_csv
    assert len(list(accel_samples_from_csv(tmp_path / "walk"))) == 25 + 4 * 30


@pytest.mark.skipif(shutil.which("micropython") is None, reason="нет micropython (brew install micropython)")
def test_wokwi_files_run_under_micropython(tmp_path):
    """main.py + checks.py + драйвер в настоящем MicroPython; I2C подменён словарём регистров."""
    shutil.copy(os.path.join(ROOT, "wokwi", "checks.py"), tmp_path)
    shutil.copy(os.path.join(ROOT, "device", "drivers", "mpu6050.py"), tmp_path)
    main = open(os.path.join(ROOT, "wokwi", "main.py"), encoding="utf-8").read()
    (tmp_path / "main.py").write_text(main.replace("STREAM_SECONDS = 60", "STREAM_SECONDS = 0.2"), encoding="utf-8")
    (tmp_path / "machine.py").write_text(
        "class Pin:\n"
        "    def __init__(self, n): pass\n"
        "class I2C:\n"
        "    def __init__(self, *a, **k): self.r = {0x75: 0x68, 0x6B: 0x40, 0x1C: 0}\n"
        "    def scan(self): return [0x68]\n"
        "    def readfrom_mem(self, addr, reg, n):\n"
        "        if reg != 0x3B: return bytes([self.r.get(reg, 0)])\n"
        "        if self.r[0x6B] & 0x40: return bytes(6)\n"
        "        lsb = (16384, 8192, 4096, 2048)[(self.r[0x1C] >> 3) & 3]\n"
        "        return bytes([0, 0, 0, 0, lsb >> 8, lsb & 0xFF])\n"
        "    def writeto_mem(self, addr, reg, data): self.r[reg] = data[0]\n",
        encoding="utf-8",
    )
    out = subprocess.run(["micropython", "main.py"], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "RESULT 6/6" in out.stdout
    assert "CSV-END" in out.stdout
