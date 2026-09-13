"""Генераторы синтетических потоков для виртуальных чипов (PI-02/PI-03):
поток ускорения (имитация акселерометра при покое/ходьбе/беге) и ИК/красная
пульсовая волна (имитация фотоплетизмографа). Параметры берутся из
`device.virtual.scenarios.Segment` — длительность, шаги/мин, ЧСС, шум.

Время — только через `Clock.now()` (`device/clock.py`), без прямых
`time.sleep`/`time.monotonic`: это требование `docs/pi.md` §3.6 и спеки
PI-04. Собственная временная шкала потока (`t = i / sample_rate_hz`)
синтетическая и не зависит от скорости вызова — ни одна функция здесь не
обращается к `time` напрямую.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterator

from device.clock import Clock
from device.virtual.scenarios import Segment

# Модуль вектора ускорения в состоянии покоя близко к 1g (чип лежит
# горизонтально). Выбрано самостоятельно для синтетики, не датчик —
# TODO(datasheet) не требуется.
_BASE_G = 1.0

# Высота всплеска ускорения на каждом шаге поверх базовой 1g и доля периода
# шага, которую этот всплеск занимает по времени (остальное время — плоская
# база + шум). Выбрано самостоятельно для синтетики.
_STEP_BURST_AMPLITUDE_G = 0.4
_STEP_BURST_WIDTH_FRACTION = 0.25

# Условные DC-уровень и AC-амплитуды ИК/красного каналов пульсоксиметра.
# Абсолютные числа выбраны самостоятельно для синтетики (не калибровка
# реального MAX30102 — это AC/DC-пропорции тока LED1_PA/LED2_PA, задача
# PI-03/даташит); IR получает большую AC-амплитуду, чем RED, как у
# реального датчика, где пульсовая компонента в IR-канале обычно выражена
# сильнее.
_PPG_DC = 50_000
_PPG_IR_AC_AMPLITUDE = 2_000
_PPG_RED_AC_AMPLITUDE = 1_200


def accel_samples(
    segment: Segment,
    sample_rate_hz: float,
    clock: Clock | None = None,
) -> Iterator[tuple[float, float, float]]:
    """Поток отсчётов ускорения (X, Y, Z) в g на длительность `segment`.

    Модуль вектора держится около 1g с периодическими всплесками на частоте
    шагов из `segment.steps_per_minute`. Приём «модуль вектора + пики с
    порогом и минимальным интервалом» — алгоритм-потребитель, описанный в
    `docs/pi.md` §7 (внутренний источник, не внешний стандарт).

    Весь всплеск размещён в оси X (условно — направление ходьбы), оси Y/Z
    несут только шум: так простой счётчик пиков по любой из осей или по
    модулю вектора видит один пик на шаг.

    `clock` принимается для совместимости с вызывающим кодом (PI-02/PI-03),
    который может делить общий `Clock` между несколькими генераторами/
    виртуальными чипами; сам поток этот параметр не использует — темп
    генерации синтетический (`i / sample_rate_hz`), без `time.sleep`.
    """
    _ = clock  # зарезервировано для будущего использования PI-02/PI-03, см. docstring

    period_s = 1.0 / sample_rate_hz
    n_samples = max(1, round(segment.duration_s * sample_rate_hz))

    step_period_s: float | None = None
    if segment.steps_per_minute > 0:
        step_period_s = 60.0 / segment.steps_per_minute

    for i in range(n_samples):
        t = i * period_s
        burst = 0.0
        if step_period_s is not None:
            phase = (t % step_period_s) / step_period_s
            if phase < _STEP_BURST_WIDTH_FRACTION:
                burst = _STEP_BURST_AMPLITUDE_G * math.sin(
                    math.pi * phase / _STEP_BURST_WIDTH_FRACTION
                )
        x = _BASE_G + burst + random.uniform(-segment.noise_level, segment.noise_level)
        y = random.uniform(-segment.noise_level, segment.noise_level)
        z = random.uniform(-segment.noise_level, segment.noise_level)
        yield (x, y, z)


def ppg_samples(segment: Segment, sample_rate_hz: float) -> Iterator[tuple[int, int]]:
    """Поток отсчётов (ir, red) фотоплетизмографа на длительность `segment`.

    Модель «постоянная составляющая (DC) + пульсовая (AC) составляющая на
    частоте ЧСС + шум» — стандартное разложение PPG-сигнала в
    биомедицинской литературе, не наша придумка: см. City, University of
    London (открытый доступ) — https://openaccess.city.ac.uk/11712
    (явно описывает AC/DC-разложение PPG-сигнала).
    """
    n_samples = max(1, round(segment.duration_s * sample_rate_hz))
    period_s = 1.0 / sample_rate_hz
    hr_hz = segment.heart_rate_bpm / 60.0

    for i in range(n_samples):
        t = i * period_s
        phase = 2.0 * math.pi * hr_hz * t
        ir_noise = random.uniform(-1.0, 1.0) * segment.noise_level * _PPG_IR_AC_AMPLITUDE
        red_noise = random.uniform(-1.0, 1.0) * segment.noise_level * _PPG_RED_AC_AMPLITUDE
        ir = _PPG_DC + _PPG_IR_AC_AMPLITUDE * math.sin(phase) + ir_noise
        red = _PPG_DC + _PPG_RED_AC_AMPLITUDE * math.sin(phase) + red_noise
        yield (round(ir), round(red))
