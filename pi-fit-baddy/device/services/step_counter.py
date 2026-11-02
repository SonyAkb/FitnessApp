"""Подсчёт шагов на потоке отсчётов акселерометра (PI-06, `docs/pi.md` §7).

Источник приёмов: Analog Devices, "Full-Featured Pedometer Design Realized
with 3-Axis Digital Accelerometer",
https://www.analog.com/en/resources/analog-dialogue/articles/pedometer-design-3-axis-digital-acceler.html

Оттуда взято: модуль вектора ускорения (не зависит от ориентации датчика),
сглаживание усреднением соседних отсчётов, амплитудный порог плюс минимальное
время между шагами для отсечения ложных срабатываний.

Своё (в статье иначе): фиксированный порог из конфига вместо динамического,
гравитация как константа 1 g, окно сглаживания 3 отсчёта по умолчанию,
causal-усреднение (только прошлые отсчёты — работаем на потоке), поиск
локального максимума с решением на отсчёт позже. Числовые параметры —
стартовые значения для синтетики, подбираются на плате в PI-10.

Время берётся только из внедряемого `Clock`; режимов mock/real сервис не знает.
"""

from __future__ import annotations

import math
from collections import deque

from device.clock import Clock
from device.config import Config

_GRAVITY_G = 1.0
_EPS_S = 1e-9  # допуск на накопленную погрешность float во времени


class StepCounter:
    """Потоковый счётчик шагов: один отсчёт `(x, y, z)` в g за вызов."""

    def __init__(
        self,
        clock: Clock,
        threshold_g: float,
        min_interval_ms: float,
        smoothing_samples: int,
    ) -> None:
        if smoothing_samples < 1:
            raise ValueError("smoothing_samples должен быть >= 1")
        self._clock = clock
        self._threshold_g = threshold_g
        self._min_interval_s = min_interval_ms / 1000.0
        self._smoothing_samples = smoothing_samples
        self._window: deque[float] = deque(maxlen=smoothing_samples)
        self._prev2: float | None = None  # сглаженное значение позапрошлого отсчёта
        self._prev: float | None = None  # сглаженное значение прошлого отсчёта
        self._prev_time: float = 0.0  # метка прошлого отсчёта
        self._last_step_time: float | None = None
        self._armed = True  # False, пока сигнал после засчитанного шага не упал ниже порога
        self._steps = 0

    @classmethod
    def from_config(cls, config: Config, clock: Clock) -> StepCounter:
        return cls(
            clock,
            threshold_g=config.step_threshold_g,
            min_interval_ms=config.step_min_interval_ms,
            smoothing_samples=config.step_smoothing_samples,
        )

    @property
    def steps(self) -> int:
        return self._steps

    def update(self, sample: tuple[float, float, float]) -> int:
        """Принимает один отсчёт `(x, y, z)` в g и возвращает накопленное число шагов.

        Порядок осей любой: используется модуль вектора, ориентация датчика
        не важна. Счёт отстаёт на один отсчёт: пик подтверждается только
        следующим отсчётом, поэтому последний пик оборвавшегося потока не
        засчитывается. Сброса «хвоста» (flush) намеренно нет — живой поток
        не заканчивается.
        """
        now = self._clock.now()
        x, y, z = sample
        dynamic = math.sqrt(x * x + y * y + z * z) - _GRAVITY_G
        self._window.append(dynamic)
        smoothed = sum(self._window) / len(self._window)

        # Максимум зафиксирован на прошлом отсчёте: он выше позапрошлого и не
        # ниже текущего (одно плато даёт один пик, так как у следующего
        # отсчёта «позапрошлое» уже не меньше).

        # Один всплеск — один шаг: после шага новый пик возможен только когда
        # сглаженный сигнал опустился до порога (иначе рябь шума на вершине
        # длинного всплеска даёт лишние шаги). Это наше собственное дополнение,
        # в статье Analog Devices такого правила нет.
        if smoothed <= self._threshold_g:
            self._armed = True

        if (
            self._armed
            and self._prev is not None
            and self._prev2 is not None
            and self._prev > self._prev2
            and self._prev >= smoothed
            and self._prev > self._threshold_g
            and (
                self._last_step_time is None
                or self._prev_time - self._last_step_time >= self._min_interval_s - _EPS_S
            )
        ):
            self._steps += 1
            self._last_step_time = self._prev_time
            self._armed = False

        self._prev2 = self._prev
        self._prev = smoothed
        self._prev_time = now
        return self._steps

    def reset(self) -> None:
        """Сбрасывает счётчик и всё состояние потока."""
        self._window.clear()
        self._prev2 = None
        self._prev = None
        self._prev_time = 0.0
        self._last_step_time = None
        self._armed = True
        self._steps = 0
