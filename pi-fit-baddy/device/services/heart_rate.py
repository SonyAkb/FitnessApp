"""Оценка ЧСС на потоке ИК-отсчётов фотоплетизмографа (PI-07, `docs/pi.md` §7).

Источники:
- AC/DC-разложение PPG-сигнала (постоянная составляющая + пульсовая),
  City, University of London, https://openaccess.city.ac.uk/11712
- полосовая фильтрация, поиск пиков и проверка согласованности межударных
  интервалов: "Robust Heart Rate Detection via Multi-Site Photoplethysmography",
  https://arxiv.org/pdf/2412.17538

Оттуда взято: сигнал раскладывается на DC и AC, AC фильтруется в полосе
пульса, ЧСС получается из интервалов между пиками, а ненадёжные интервалы
отсекаются проверкой согласованности (в статье порог 0.51 для отношения
интервалов).

Своё (в источниках иначе): вместо фильтра Баттерворта, который обычно
используют в литературе, простой каскад из двух экспоненциальных средних
(медленное вычитает DC на `band_low_hz`, быстрое сглаживает на `band_high_hz`);
он устойчив и обходится без внешних зависимостей (numpy/scipy). Коэффициенты
считаются по реальному шагу `dt` между метками `Clock`, поэтому алгоритм не
привязан к частоте опроса. Доля пика 0.5 от максимума в окне, минимум 4 пика,
порог согласованности 0.5, дополнительный предел отклонения интервала от
медианы 25 % (отсекает случайный шум) и перфузионное отношение `(макс-мин)/2 / DC` как мера
слабого сигнала — наши решения. Все числа — стартовые значения для синтетики,
подбираются на плате в PI-10.

Время берётся только из внедряемого `Clock`; режимов mock/real сервис не знает.
Только ИК-канал, красный не используется. При ненадёжном сигнале результат
`None`, а не выдуманное число. Оценка запаздывает на один отсчёт: пик
подтверждается следующим отсчётом.
"""

from __future__ import annotations

import math
import statistics
from collections import deque
from itertools import pairwise

from device.clock import Clock
from device.config import Config

_PEAK_FRACTION = 0.5  # пик не ниже этой доли максимума отфильтрованного сигнала в окне
_MIN_PEAKS = 4  # 4 пика = 3 межпиковых интервала
# min/max интервалов в окне, ниже — нерегулярность. В статье порог 0.51 для
# соседних интервалов; у нас 0.5 на всё окно — круглое стартовое значение для
# синтетики, подбирается на плате в PI-10.
_MIN_INTERVAL_RATIO = 0.5
# Допустимый диапазон ЧСС: бэкенд отклоняет heart_rate вне 30-230 ответом 422
# (docs/API_CONTRACT.md, POST /telemetry/ingest), поэтому вне диапазона - None.
_MIN_BPM = 30
_MAX_BPM = 230
# Своё, сверх проверки min/max: каждый интервал не дальше этой доли от медианы.
# Без неё случайный шум изредка даёт 4 пика с отношением min/max чуть выше 0.5.
_MAX_DEVIATION = 0.25
_EPS_S = 1e-9  # допуск на накопленную погрешность float во времени


def _alpha(freq_hz: float, dt: float) -> float:
    """Коэффициент экспоненциального среднего со срезом `freq_hz` при шаге `dt`."""
    return 1.0 - math.exp(-2.0 * math.pi * freq_hz * dt)


class HeartRateEstimator:
    """Потоковая оценка ЧСС: один ИК-отсчёт за вызов, состояние между вызовами."""

    def __init__(
        self,
        clock: Clock,
        band_low_hz: float,
        band_high_hz: float,
        window_s: float,
        min_signal_ratio: float,
    ) -> None:
        if not 0 < band_low_hz < band_high_hz:
            raise ValueError("нужно 0 < band_low_hz < band_high_hz")
        if window_s <= 0:
            raise ValueError("window_s должен быть > 0")
        if min_signal_ratio < 0:
            raise ValueError("min_signal_ratio должен быть >= 0")
        self._clock = clock
        self._band_low_hz = band_low_hz
        self._band_high_hz = band_high_hz
        self._window_s = window_s
        self._min_signal_ratio = min_signal_ratio
        self._min_peak_gap_s = 1.0 / band_high_hz
        self.reset()

    @classmethod
    def from_config(cls, config: Config, clock: Clock) -> HeartRateEstimator:
        return cls(
            clock,
            band_low_hz=config.hr_band_hz_low,
            band_high_hz=config.hr_band_hz_high,
            window_s=config.hr_window_s,
            min_signal_ratio=config.hr_min_signal_ratio,
        )

    @property
    def heart_rate(self) -> int | None:
        return self._heart_rate

    def update(self, ir: float) -> int | None:
        """Принимает один ИК-отсчёт и возвращает ЧСС в уд/мин либо `None`.

        Если время не продвинулось (`dt <= 0`), отсчёт пропускается и текущая
        оценка не меняется.
        """
        now = self._clock.now()
        if self._prev_time is None:
            self._dc = float(ir)
            self._filtered = 0.0
            self._first_time = now
            self._prev_time = now
            return self._heart_rate
        dt = now - self._prev_time
        if dt <= 0:
            return self._heart_rate
        self._prev_time = now

        # Убираем DC медленным средним, затем сглаживаем верхние частоты.
        self._dc += _alpha(self._band_low_hz, dt) * (ir - self._dc)
        ac = ir - self._dc
        self._filtered += _alpha(self._band_high_hz, dt) * (ac - self._filtered)
        value = self._filtered

        horizon = now - self._window_s
        self._values.append((now, value))
        while self._values and self._values[0][0] < horizon:
            self._values.popleft()

        # Максимум подтверждается следующим отсчётом (запаздывание на отсчёт).
        if self._prev is not None and self._prev2 is not None:
            p_time, p_val = self._prev_time_val, self._prev
            if p_val > self._prev2 and p_val >= value and p_val > 0:
                window_max = max(v for _, v in self._values)
                far_enough = (
                    not self._peaks
                    or p_time - self._peaks[-1][0] >= self._min_peak_gap_s - _EPS_S
                )
                if p_val >= _PEAK_FRACTION * window_max and far_enough:
                    self._peaks.append((p_time, p_val))
        while self._peaks and self._peaks[0][0] < horizon:
            self._peaks.popleft()

        self._prev2 = self._prev
        self._prev = value
        self._prev_time_val = now

        self._heart_rate = self._estimate(now)
        return self._heart_rate

    def _estimate(self, now: float) -> int | None:
        # (1) окно ещё не накоплено или мало пиков
        if self._first_time is None or now - self._first_time < self._window_s - _EPS_S:
            return None
        if len(self._peaks) < _MIN_PEAKS:
            return None
        # (3) датчик ничего не видит
        if self._dc <= 0:
            return None
        # (2) слабый сигнал: перфузионное отношение (макс-мин)/2 / DC
        values = [v for _, v in self._values]
        if (max(values) - min(values)) / 2.0 / self._dc < self._min_signal_ratio:
            return None
        times = [t for t, _ in self._peaks]
        intervals = [b - a for a, b in pairwise(times)]
        # (4) нерегулярность интервалов
        if min(intervals) / max(intervals) < _MIN_INTERVAL_RATIO:
            return None
        median = statistics.median(intervals)
        if max(abs(i - median) for i in intervals) > _MAX_DEVIATION * median:
            return None
        bpm = round(60.0 / median)
        if not _MIN_BPM <= bpm <= _MAX_BPM:
            return None
        return bpm

    def reset(self) -> None:
        """Сбрасывает оценку и всё состояние потока."""
        self._dc = 0.0
        self._filtered = 0.0
        self._prev_time: float | None = None
        self._first_time: float | None = None
        self._prev: float | None = None
        self._prev2: float | None = None
        self._prev_time_val = 0.0  # метка отсчёта `_prev`
        self._values: deque[tuple[float, float]] = deque()
        self._peaks: deque[tuple[float, float]] = deque()
        self._heart_rate: int | None = None
