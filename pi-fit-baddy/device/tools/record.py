"""Запись CSV с датчиков: `python -m device.tools.record --seconds N --out PREFIX`.

Использует тот же путь, что и сервис: `load_config()` -> `create_bus(config)` ->
драйверы `Mpu6050` / `Max30102`. Режим (`mock` / `real`) определяется только
переменной `SENSOR_MODE` внутри `create_bus`; здесь веток по режиму нет.

Выходные файлы (формат, который читает `device/virtual/csv_player.py`):
  <PREFIX>_accel.csv  заголовок `t,x,y,z`  (ускорение в g)
  <PREFIX>_ppg.csv    заголовок `t,ir,red` (сырые отсчёты MAX30102)
`t` — секунды от начала записи по `Clock`.

Коды возврата: 0 — готово; 1 — ошибка шины / датчика / записи файлов; 2 — неверные
аргументы или выходные файлы уже существуют (без `--force`); 130 — Ctrl+C
(записанные строки сохраняются).
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO

from device.bus.factory import create_bus
from device.clock import Clock, MonotonicClock
from device.config import Config, load_config
from device.drivers.max30102 import Max30102
from device.drivers.mpu6050 import Mpu6050

ACCEL_HEADER = "t,x,y,z"
PPG_HEADER = "t,ir,red"


class _ArgumentError(Exception):
    """Неверные аргументы командной строки."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):  # type: ignore[override]
        raise _ArgumentError(message)


def _positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"не число: {text!r}") from None
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(f"должно быть > 0, получено {text!r}")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="python -m device.tools.record",
        description="Запись CSV с акселерометра и пульсометра (формат csv_player).",
    )
    parser.add_argument(
        "--seconds", type=_positive_float, required=True, help="длительность, с (> 0)"
    )
    parser.add_argument(
        "--out", required=True, help="префикс файлов: <PREFIX>_accel.csv, <PREFIX>_ppg.csv"
    )
    parser.add_argument(
        "--force", action="store_true", help="перезаписать существующие файлы"
    )
    return parser


def _fmt(value: float) -> str:
    return format(value, ".10g")


def _record(
    mpu: Mpu6050,
    max_sensor: Max30102,
    accel_file: TextIO,
    ppg_file: TextIO,
    *,
    ticks: int,
    rate: float,
    clock: Clock,
    sleep: Callable[[float], Any],
    counts: list[float],
) -> None:
    """counts: [строк accel, строк ppg, время последнего тика от начала, с]."""
    period = 1.0 / rate
    start = clock.now()
    last_ppg_t = 0.0
    next_at = start
    for _ in range(ticks):
        # Расписание от начала записи без накопления дрейфа. При отставании
        # серия тиков для догоняния не запускается: целиком пропущенные слоты
        # сетки start + i * period отбрасываются, одно опоздавшее чтение идёт
        # сразу, затем расписание возвращается на сетку (sleep никогда не
        # вызывается с неположительным значением).
        lag = clock.now() - next_at
        missed = math.floor(lag / period + 1e-9)
        if missed > 0:
            next_at += missed * period
        delay = next_at - clock.now()
        if delay > 0:
            sleep(delay)
        next_at += period
        t = clock.now() - start
        counts[2] = t
        x, y, z = mpu.read_acceleration_g()
        accel_file.write(f"{_fmt(t)},{_fmt(x)},{_fmt(y)},{_fmt(z)}\n")
        counts[0] += 1

        available = max_sensor.available_samples()
        if available > 0:
            samples = max_sensor.read_fifo_samples(available)
            n = len(samples)
            for j, (red, ir) in enumerate(samples):
                # Собственное решение: у отсчётов одного тика нет своей метки,
                # поэтому они равномерно отодвигаются назад от момента тика с
                # шагом 1 / sample_rate_hz (последний отсчёт — в момент тика) и
                # не убывают (не раньше предыдущей записанной метки).
                ts = max(t - (n - 1 - j) * period, last_ppg_t)
                last_ppg_t = ts
                # Драйвер отдаёт (red, ir), в файл пишем ir, red.
                ppg_file.write(f"{_fmt(ts)},{ir},{red}\n")
                counts[1] += 1


def main(
    argv: Sequence[str] | None = None,
    *,
    config: Config | None = None,
    clock: Clock | None = None,
    sleep: Callable[[float], Any] = time.sleep,
    bus: Any = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        args = _build_parser().parse_args(argv)
    except _ArgumentError as exc:
        print(f"Ошибка аргументов: {exc}", file=err)
        return 2
    except SystemExit:  # --help
        return 0

    prefix = str(args.out)
    if not prefix.strip() or prefix.endswith(("/", os.sep)) or (
        os.altsep is not None and prefix.endswith(os.altsep)
    ):
        print(
            "Ошибка аргументов: --out должен быть префиксом файла, а не пустым "
            "значением или каталогом (например, data/walk).",
            file=err,
        )
        return 2
    accel_path = Path(f"{prefix}_accel.csv")
    ppg_path = Path(f"{prefix}_ppg.csv")
    existing = [str(p) for p in (accel_path, ppg_path) if p.exists()]
    if existing and not args.force:
        print(
            "Файлы уже существуют, ничего не записано: "
            + ", ".join(existing)
            + ". Задайте другой --out или --force для перезаписи.",
            file=err,
        )
        return 2

    try:
        cfg = config or load_config()
        active_clock = clock or MonotonicClock()
        active_bus = bus if bus is not None else create_bus(cfg)
        mpu = Mpu6050(active_bus, cfg.mpu6050_addr)
        max_sensor = Max30102(active_bus, cfg.max30102_addr)
        # Те же вызовы подготовки, что и в сервисе (Sampler).
        mpu.wake()
        max_sensor.initialize()
    except (OSError, ImportError, ValueError) as exc:
        print(f"Не удалось подготовить датчики: {exc}", file=err)
        return 1

    ticks = max(1, round(args.seconds * cfg.sample_rate_hz))
    counts: list[float] = [0, 0, 0.0]
    code = 0
    try:
        accel_path.parent.mkdir(parents=True, exist_ok=True)
        with accel_path.open("w", newline="") as accel_file, ppg_path.open(
            "w", newline=""
        ) as ppg_file:
            accel_file.write(ACCEL_HEADER + "\n")
            ppg_file.write(PPG_HEADER + "\n")
            try:
                _record(
                    mpu,
                    max_sensor,
                    accel_file,
                    ppg_file,
                    ticks=ticks,
                    rate=cfg.sample_rate_hz,
                    clock=active_clock,
                    sleep=sleep,
                    counts=counts,
                )
            except KeyboardInterrupt:
                print("Запись прервана (Ctrl+C).", file=err)
                code = 130
            except OSError as exc:
                print(
                    f"Ошибка шины, запись прервана: {exc}. "
                    "Уже записанные строки сохранены.",
                    file=err,
                )
                code = 1
            except Exception as exc:  # noqa: BLE001 - сохраняем записанное
                print(
                    f"Непредвиденная ошибка, запись прервана: "
                    f"{type(exc).__name__}: {exc}. Уже записанные строки сохранены.",
                    file=err,
                )
                code = 1
    except OSError as exc:  # каталог / файл недоступны для записи
        print(f"Не удалось записать файлы: {exc}", file=err)
        return 1

    print(
        f"Записано строк: {counts[0]} -> {accel_path}, {counts[1]} -> {ppg_path}",
        file=out,
    )
    elapsed = counts[2]
    if counts[0] > 1 and elapsed > 0:
        effective = (counts[0] - 1) / elapsed
        print(
            f"Длительность {elapsed:.2f} с, фактическая частота {effective:.1f} Гц "
            f"(задано {cfg.sample_rate_hz:g} Гц).",
            file=out,
        )
        if effective < 0.95 * cfg.sample_rate_hz:
            print(
                "Предупреждение: запись шла с отставанием от расписания; "
                "проигрыватель CSV игнорирует колонку t и воспроизведёт её "
                "с неверной скоростью.",
                file=err,
            )
    try:
        if max_sensor.overflow_count() > 0:
            print(
                "Предупреждение: FIFO переполнялся: в ppg возможны пропуски.",
                file=err,
            )
    except OSError:
        pass
    return code


if __name__ == "__main__":
    sys.exit(main())
