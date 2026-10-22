"""Тесты device/tools/record.py: формат, круг «запись -> алгоритмы», защита данных."""

from __future__ import annotations

import dataclasses
import io
import math

import pytest

from device.bus.factory import create_bus
from device.clock import ManualClock
from device.config import load_config
from device.services.heart_rate import HeartRateEstimator
from device.services.step_counter import StepCounter
from device.tools import record
from device.virtual.csv_player import accel_samples_from_csv, ppg_samples_from_csv


class Run:
    """Запуск main с ManualClock и фейковым sleep, перехватом вывода."""

    def __init__(self, tmp_path, scenario="walk", **overrides):
        self.config = dataclasses.replace(
            load_config(), sensor_mode="mock", scenario=scenario, **overrides
        )
        self.clock = ManualClock()
        self.prefix = str(tmp_path / "rec")
        self.out = io.StringIO()
        self.err = io.StringIO()

    def sleep(self, seconds):
        self.clock.advance(seconds)

    def main(self, *argv, bus=None):
        return record.main(
            list(argv),
            config=self.config,
            clock=self.clock,
            sleep=self.sleep,
            bus=bus,
            stdout=self.out,
            stderr=self.err,
        )

    def record(self, seconds, *extra, bus=None):
        return self.main("--seconds", str(seconds), "--out", self.prefix, *extra, bus=bus)


def _lines(path):
    return path.read_text().splitlines()


def test_files_headers_rows_and_monotonic_time(tmp_path):
    run = Run(tmp_path)
    assert run.record(10) == 0

    accel = _lines(tmp_path / "rec_accel.csv")
    ppg = _lines(tmp_path / "rec_ppg.csv")
    assert accel[0] == "t,x,y,z"
    assert ppg[0] == "t,ir,red"
    assert len(accel) - 1 == 500
    # Виртуальный чип на первом чтении указателя ещё пуст: допускаем на 1 меньше.
    assert 499 <= len(ppg) - 1 <= 500
    for lines in (accel, ppg):
        times = [float(line.split(",")[0]) for line in lines[1:]]
        assert times[0] >= 0.0
        assert all(b >= a for a, b in zip(times, times[1:]))
    assert "500 ->" in run.out.getvalue()


def test_files_readable_by_csv_player(tmp_path):
    run = Run(tmp_path)
    run.record(2)
    accel = list(accel_samples_from_csv(run.prefix))
    ppg = list(ppg_samples_from_csv(run.prefix))
    assert len(accel) == 100
    assert 99 <= len(ppg) <= 100
    assert all(len(row) == 4 for row in accel)
    assert all(len(row) == 3 for row in ppg)


def test_ir_and_red_channels_not_swapped(tmp_path):
    run = Run(tmp_path)
    run.record(10)
    ppg = list(ppg_samples_from_csv(run.prefix))
    irs = [ir for _t, ir, _red in ppg]
    reds = [red for _t, _ir, red in ppg]
    assert max(irs) - min(irs) > max(reds) - min(reds)


def test_round_trip_steps_and_heart_rate(tmp_path):
    run = Run(tmp_path)
    assert run.record(60) == 0

    cfg = run.config
    dt = 1.0 / cfg.sample_rate_hz
    clock = ManualClock()
    steps = StepCounter.from_config(cfg, clock)
    for _t, x, y, z in accel_samples_from_csv(run.prefix):
        clock.advance(dt)
        steps.update((x, y, z))
    assert 95 <= steps.steps <= 105  # ~100 шагов за 60 с walk, +-5 %

    hr_clock = ManualClock()
    estimator = HeartRateEstimator.from_config(cfg, hr_clock)
    for _t, ir, _red in ppg_samples_from_csv(run.prefix):
        hr_clock.advance(dt)
        estimator.update(ir)
    assert estimator.heart_rate is not None
    assert abs(estimator.heart_rate - 95) <= 3


def test_existing_files_not_overwritten_without_force(tmp_path):
    run = Run(tmp_path)
    accel = tmp_path / "rec_accel.csv"
    accel.write_text("keep")
    assert run.record(1) == 2
    assert accel.read_text() == "keep"
    assert not (tmp_path / "rec_ppg.csv").exists()
    assert "--force" in run.err.getvalue()


def test_force_overwrites(tmp_path):
    run = Run(tmp_path)
    (tmp_path / "rec_accel.csv").write_text("old")
    (tmp_path / "rec_ppg.csv").write_text("old")
    assert run.record(1, "--force") == 0
    assert _lines(tmp_path / "rec_accel.csv")[0] == "t,x,y,z"
    assert _lines(tmp_path / "rec_ppg.csv")[0] == "t,ir,red"


def test_creates_missing_directory(tmp_path):
    run = Run(tmp_path)
    run.prefix = str(tmp_path / "new" / "dir" / "x")
    assert run.record(1) == 0
    assert (tmp_path / "new" / "dir" / "x_accel.csv").is_file()


@pytest.mark.parametrize("seconds", ["0", "-5", "abc", "nan", "inf"])
def test_bad_seconds(tmp_path, seconds):
    run = Run(tmp_path)
    assert run.record(seconds) == 2
    assert run.err.getvalue()
    assert list(tmp_path.iterdir()) == []


def test_missing_arguments(tmp_path):
    run = Run(tmp_path)
    assert run.main("--seconds", "1") == 2
    assert list(tmp_path.iterdir()) == []


class FlakyBus:
    """Шина-обёртка: после N чтений блока бросает OSError(121)."""

    def __init__(self, inner, fail_after):
        self._inner = inner
        self._left = fail_after

    def write_byte_data(self, *a):
        return self._inner.write_byte_data(*a)

    def read_byte_data(self, *a):
        return self._inner.read_byte_data(*a)

    def read_i2c_block_data(self, *a):
        if self._left <= 0:
            raise OSError(121, "Remote I/O error")
        self._left -= 1
        return self._inner.read_i2c_block_data(*a)


def test_oserror_mid_recording_keeps_written_rows(tmp_path):
    run = Run(tmp_path)
    bus = FlakyBus(create_bus(run.config), fail_after=40)
    assert run.record(10, bus=bus) == 1
    assert "Remote I/O error" in run.err.getvalue()
    accel = _lines(tmp_path / "rec_accel.csv")
    assert accel[0] == "t,x,y,z"
    assert 1 < len(accel) < 501
    assert len(_lines(tmp_path / "rec_ppg.csv")) > 1


class DeadBus:
    """Шина, на которой не отвечает ни один регистр."""

    def write_byte_data(self, *a):
        raise OSError(121, "Remote I/O error")

    read_byte_data = read_i2c_block_data = write_byte_data


def test_oserror_at_init_returns_1_without_files(tmp_path):
    run = Run(tmp_path)
    assert run.record(1, bus=DeadBus()) == 1
    assert list(tmp_path.iterdir()) == []


class BurstBus:
    """Шина с фиксированным накоплением: FIFO отдаёт по 3 отсчёта за тик."""

    def write_byte_data(self, addr, reg, val):
        pass

    def read_byte_data(self, addr, reg):
        return 0

    def read_i2c_block_data(self, addr, reg, length):
        if addr == 0x68:
            return [0, 0, 0, 0, 0x40, 0]  # z = 16384 -> 1 g при +-2 g
        if reg == 0x04:
            return [3, 0, 0]  # WR=3, RD=0 -> 3 отсчёта
        return [0, 0, 1, 0, 0, 2] * (length // 6)  # red=1, ir=2


def test_several_samples_per_tick_are_spaced_back_and_non_decreasing(tmp_path):
    run = Run(tmp_path)
    assert run.record(1, bus=BurstBus()) == 0
    ppg = list(ppg_samples_from_csv(run.prefix))
    assert len(ppg) == 3 * 50
    times = [t for t, _ir, _red in ppg]
    assert all(b >= a for a, b in zip(times, times[1:]))
    # Первый тик (t = 0): все три метки зажаты нулём.
    assert times[0:3] == pytest.approx([0.0, 0.0, 0.0])
    # Второй тик (t = 0.02): -0.02 зажато нулём, затем 0.0 и 0.02.
    assert times[3:6] == pytest.approx([0.0, 0.0, 0.02])
    # Третий тик (t = 0.04): 0.00 зажато предыдущей меткой 0.02, затем 0.02, 0.04.
    assert times[6:9] == pytest.approx([0.02, 0.02, 0.04])
    assert all((ir, red) == (2, 1) for _t, ir, red in ppg)


class WrapBus:
    """Обёртка над шиной с переопределяемым поведением."""

    def __init__(self, inner, *, on_block=None, ovf=0):
        self._inner = inner
        self._on_block = on_block
        self._ovf = ovf

    def write_byte_data(self, *a):
        return self._inner.write_byte_data(*a)

    def read_byte_data(self, addr, reg):
        if reg == 0x05 and self._ovf:
            return self._ovf
        return self._inner.read_byte_data(addr, reg)

    def read_i2c_block_data(self, *a):
        if self._on_block:
            self._on_block()
        return self._inner.read_i2c_block_data(*a)


def test_help_returns_0(tmp_path, capsys):
    run = Run(tmp_path)
    assert run.main("--help") == 0
    assert "--seconds" in capsys.readouterr().out


def test_create_bus_import_error_returns_1(tmp_path, monkeypatch):
    run = Run(tmp_path)

    def boom(_config):
        raise ImportError("No module named 'smbus2'")

    monkeypatch.setattr(record, "create_bus", boom)
    assert run.record(1) == 1
    assert "smbus2" in run.err.getvalue()
    assert list(tmp_path.iterdir()) == []


def test_out_under_regular_file_returns_1(tmp_path):
    run = Run(tmp_path)
    blocker = tmp_path / "file"
    blocker.write_text("x")
    run.prefix = str(blocker / "sub" / "x")
    assert run.record(1) == 1
    assert run.err.getvalue()


def test_keyboard_interrupt_returns_130_and_keeps_rows(tmp_path):
    run = Run(tmp_path)
    calls = {"n": 0}

    def interrupt():
        calls["n"] += 1
        if calls["n"] > 30:
            raise KeyboardInterrupt

    bus = WrapBus(create_bus(run.config), on_block=interrupt)
    assert run.record(10, bus=bus) == 130
    assert len(_lines(tmp_path / "rec_accel.csv")) > 5
    assert "Записано строк" in run.out.getvalue()


def test_unexpected_exception_returns_1_and_keeps_rows(tmp_path):
    run = Run(tmp_path)
    calls = {"n": 0}

    def fail():
        calls["n"] += 1
        if calls["n"] > 30:
            raise RuntimeError("странный сбой")

    bus = WrapBus(create_bus(run.config), on_block=fail)
    assert run.record(10, bus=bus) == 1
    assert "странный сбой" in run.err.getvalue()
    assert len(_lines(tmp_path / "rec_accel.csv")) > 5


def test_overflow_warning(tmp_path):
    run = Run(tmp_path)
    assert run.record(1, bus=WrapBus(create_bus(run.config), ovf=3)) == 0
    assert "FIFO переполнялся" in run.err.getvalue()


def test_no_overflow_no_warning(tmp_path):
    run = Run(tmp_path)
    assert run.record(1) == 0
    assert "переполнялся" not in run.err.getvalue()
    assert "отставанием" not in run.err.getvalue()


@pytest.mark.parametrize("out", ["", "  ", "data/", "a/b/"])
def test_bad_out_returns_2(tmp_path, out):
    run = Run(tmp_path)
    assert run.main("--seconds", "1", "--out", out) == 2
    assert list(tmp_path.iterdir()) == []


def test_lag_does_not_burst_and_returns_to_grid(tmp_path):
    run = Run(tmp_path)
    period = 1.0 / run.config.sample_rate_hz
    sleeps = []
    reads = {"n": 0}

    def slow_read():
        reads["n"] += 1
        if reads["n"] == 20:  # одно чтение занимает 8.5 периода
            run.clock.advance(8.5 * period)

    def sleep(seconds):
        sleeps.append(seconds)
        run.clock.advance(seconds)

    run.sleep = sleep
    bus = WrapBus(create_bus(run.config), on_block=slow_read)
    assert run.record(2, bus=bus) == 0

    assert sleeps and all(s > 0 for s in sleeps)
    times = [
        float(line.split(",")[0]) for line in _lines(tmp_path / "rec_accel.csv")[1:]
    ]
    gaps = [b - a for a, b in zip(times, times[1:])]
    # Серии подряд идущих тиков нет: между тиками никогда меньше ~0.4 периода,
    assert min(gaps) > 0.4 * period
    # пропущенные слоты не догоняются (запись длится дольше номинальных 2 с),
    assert times[-1] > 2.0 - period
    # а хвост снова лежит на сетке i * period.
    for t in times[-10:]:
        assert math.isclose(t / period, round(t / period), abs_tol=1e-6)
    assert "отставанием" in run.err.getvalue()
