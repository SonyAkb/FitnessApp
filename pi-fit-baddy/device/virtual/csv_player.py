"""Проигрыватель записанных CSV-отсчётов — альтернатива встроенным сценариям.

Если `SCENARIO` не входит в `device.virtual.scenarios.SCENARIOS`, вызывающий
код (PI-02/PI-03) трактует его как префикс записи и читает её через функции
этого модуля, а не через `device/virtual/signals.py`.

Формат колонок (`t,x,y,z` / `t,ir,red`) и имена файлов
(`<prefix>_accel.csv` / `<prefix>_ppg.csv`) — внутренний источник, см.
`pi-fit-baddy/README.md`, раздел «Запись CSV с реальных датчиков». Сам
инструмент записи (`device/tools/record.py`) — задача PI-10 и здесь не
реализуется; эта задача отвечает только за воспроизведение уже записанных
файлов такого формата.
"""

from __future__ import annotations

import csv
import os
from collections.abc import Iterator
from pathlib import Path

PathLike = str | os.PathLike[str]


def _csv_path(prefix: PathLike, kind: str) -> Path:
    return Path(f"{prefix}_{kind}.csv")


def _looks_like_header(row: list[str]) -> bool:
    """Первая строка — заголовок, если её первая ячейка не число (`t`)."""
    try:
        float(row[0])
    except ValueError:
        return True
    return False


def _read_data_rows(path: Path, *, expected_columns: int) -> list[list[str]]:
    """Читает CSV целиком и отбрасывает заголовок, если он есть.

    Отсутствие файла (или `prefix`, указывающий на каталог, а не на файл) —
    явная, понятная ошибка (не пустой/бесшумный поток), как того требует
    задача PI-04: поднимается сразу при вызове `*_from_csv`, а
    не отложенно при первой итерации. Файл без строк данных (пустой или
    только с заголовком) — та же явная ошибка, а не молчаливый пустой поток.
    """
    kind = "accel" if expected_columns == 4 else "ppg"

    if not path.is_file():
        raise FileNotFoundError(
            f"CSV-запись не найдена: {path}. Ожидается файл формата "
            f"<prefix>_{kind}.csv "
            "(см. pi-fit-baddy/README.md, «Запись CSV с реальных датчиков»); "
            "возможно, SCENARIO указывает на несуществующую запись или на "
            "каталог вместо файла."
        )

    with path.open(newline="") as csv_file:
        rows = [row for row in csv.reader(csv_file) if row]

    if rows and _looks_like_header(rows[0]):
        rows = rows[1:]

    if not rows:
        raise ValueError(
            f"CSV-запись пуста: {path}. Ожидается хотя бы одна строка данных "
            f"формата <prefix>_{kind}.csv "
            "(см. pi-fit-baddy/README.md, «Запись CSV с реальных датчиков»); "
            "в файле нет строк данных (возможно, только заголовок)."
        )

    for row in rows:
        if len(row) != expected_columns:
            raise ValueError(
                f"Некорректная строка в {path}: ожидалось {expected_columns} "
                f"колонок, получено {len(row)}: {row!r}"
            )

    return rows


def _convert_row(
    row: list[str], path: Path, converters: tuple
) -> tuple:
    """Применяет `converters` к ячейкам строки, оборачивая ошибку разбора
    понятным сообщением с указанием файла и самой строки."""
    try:
        return tuple(convert(value) for convert, value in zip(converters, row))
    except ValueError as exc:
        raise ValueError(
            f"Некорректные данные в {path}, строка {row!r}: {exc}"
        ) from exc


def accel_samples_from_csv(prefix: PathLike) -> Iterator[tuple[float, float, float, float]]:
    """Воспроизводит `<prefix>_accel.csv` (`t,x,y,z`) в порядке строк файла."""
    path = _csv_path(prefix, "accel")
    rows = _read_data_rows(path, expected_columns=4)
    converters = (float, float, float, float)
    return iter([_convert_row(row, path, converters) for row in rows])


def ppg_samples_from_csv(prefix: PathLike) -> Iterator[tuple[float, int, int]]:
    """Воспроизводит `<prefix>_ppg.csv` (`t,ir,red`) в порядке строк файла."""
    path = _csv_path(prefix, "ppg")
    rows = _read_data_rows(path, expected_columns=3)
    converters = (float, lambda v: int(float(v)), lambda v: int(float(v)))
    return iter([_convert_row(row, path, converters) for row in rows])
