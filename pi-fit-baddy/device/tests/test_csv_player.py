"""Тесты device/virtual/csv_player.py: проигрыватель записанных CSV-отсчётов.

Записи с реальных датчиков (`device/tools/record.py`) — задача PI-10, здесь
не существуют: тесты создают временные CSV-файлы сами (tmp_path), не
зависят от несуществующего инструмента записи.
"""

import pytest

from device.virtual.csv_player import accel_samples_from_csv, ppg_samples_from_csv


def _write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(str(v) for v in row) for row in rows]
    path.write_text("\n".join(lines) + "\n")


def test_accel_samples_from_csv_replays_rows_in_file_order(tmp_path):
    prefix = tmp_path / "walk_2026-10-14"
    _write_csv(
        tmp_path / "walk_2026-10-14_accel.csv",
        ["t", "x", "y", "z"],
        [(0.0, 1.0, 0.0, 0.0), (0.02, 1.1, -0.1, 0.05), (0.04, 0.95, 0.02, -0.03)],
    )

    samples = list(accel_samples_from_csv(str(prefix)))

    assert samples == [
        (0.0, 1.0, 0.0, 0.0),
        (0.02, 1.1, -0.1, 0.05),
        (0.04, 0.95, 0.02, -0.03),
    ]


def test_ppg_samples_from_csv_replays_rows_in_file_order(tmp_path):
    prefix = tmp_path / "walk_2026-10-14"
    _write_csv(
        tmp_path / "walk_2026-10-14_ppg.csv",
        ["t", "ir", "red"],
        [(0.0, 50000, 30000), (0.02, 51234, 30500)],
    )

    samples = list(ppg_samples_from_csv(str(prefix)))

    assert samples == [(0.0, 50000, 30000), (0.02, 51234, 30500)]


def test_accel_samples_from_csv_works_without_header(tmp_path):
    prefix = tmp_path / "no_header"
    (tmp_path / "no_header_accel.csv").write_text("0.0,1.0,0.0,0.0\n0.02,1.05,0.0,0.0\n")

    samples = list(accel_samples_from_csv(str(prefix)))

    assert samples == [(0.0, 1.0, 0.0, 0.0), (0.02, 1.05, 0.0, 0.0)]


def test_accel_samples_from_csv_missing_file_raises_clear_error(tmp_path):
    prefix = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="missing_accel.csv"):
        accel_samples_from_csv(str(prefix))


def test_ppg_samples_from_csv_missing_file_raises_clear_error(tmp_path):
    prefix = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="missing_ppg.csv"):
        ppg_samples_from_csv(str(prefix))


def test_accel_samples_from_csv_directory_prefix_raises_file_not_found(tmp_path):
    # `prefix` может указывать на каталог (например, при опечатке в SCENARIO)
    # — это должно давать ту же понятную ошибку, что и отсутствующий файл,
    # а не падение внутри open() с IsADirectoryError.
    (tmp_path / "oops_accel.csv").mkdir()

    with pytest.raises(FileNotFoundError, match="oops_accel.csv"):
        accel_samples_from_csv(str(tmp_path / "oops"))


def test_accel_samples_from_csv_header_only_file_raises_clear_error(tmp_path):
    prefix = tmp_path / "empty"
    _write_csv(tmp_path / "empty_accel.csv", ["t", "x", "y", "z"], [])

    with pytest.raises(ValueError, match="пуста"):
        accel_samples_from_csv(str(prefix))


def test_accel_samples_from_csv_column_count_mismatch_raises_clear_error(tmp_path):
    prefix = tmp_path / "bad_columns"
    (tmp_path / "bad_columns_accel.csv").write_text("t,x,y,z\n0.0,1.0,0.0\n")

    with pytest.raises(ValueError, match="ожидалось 4"):
        accel_samples_from_csv(str(prefix))


def test_accel_samples_from_csv_non_numeric_cell_raises_clear_error(tmp_path):
    prefix = tmp_path / "bad_value"
    (tmp_path / "bad_value_accel.csv").write_text("t,x,y,z\n0.0,oops,0.0,0.0\n")

    with pytest.raises(ValueError, match="Некорректные данные"):
        accel_samples_from_csv(str(prefix))
