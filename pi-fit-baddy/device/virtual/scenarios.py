"""Именованные сценарии синтетики: сегменты «покой/ходьба/бег/восстановление».

Единый источник параметров для `device/virtual/signals.py` (генераторы
потока) и для тестов — чтобы DoD-тест PI-04 и будущие потребители (PI-02,
PI-03, PI-06, PI-07) не дублировали числа сегментов.

`SCENARIO` = одно из `SCENARIOS` → встроенный сценарий (эта задача).
Любое другое значение `SCENARIO` → префикс пути к CSV-записи
(`device/virtual/csv_player.py`) — это решает вызывающий код (PI-02/PI-03),
не этот модуль: здесь только реестр встроенных сценариев.

Числа сегментов (длительность, шаги/мин, ЧСС, уровень шума) нигде в
`docs/pi.md` / задаче PI-04 / README не заданы,
кроме `walk`=100 шаг/мин — это число из DoD-теста задачи PI-04
("сценарий walk на 60 с при 100 шаг/мин даёт ~100 обнаруживаемых пиков").
Остальные значения выбраны самостоятельно как простые статичные параметры
для синтетики (без динамики внутри сегмента — см. CLAUDE.md про отсутствие
переусложнения MVP), не из датчика и не из даташита, поэтому `TODO(datasheet)`
здесь не нужен.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    """Параметры одного сегмента сценария, статичные на всю длительность.

    `steps_per_minute=0` означает отсутствие шаговых всплесков (покой).
    """

    duration_s: float
    steps_per_minute: float
    heart_rate_bpm: float
    noise_level: float


# Выбрано самостоятельно для синтетики (не из datasheet/статьи), кроме
# steps_per_minute у `walk` — см. docstring модуля.
SCENARIOS: dict[str, Segment] = {
    "rest": Segment(duration_s=30.0, steps_per_minute=0.0, heart_rate_bpm=68.0, noise_level=0.02),
    "walk": Segment(duration_s=60.0, steps_per_minute=100.0, heart_rate_bpm=95.0, noise_level=0.03),
    "run": Segment(duration_s=60.0, steps_per_minute=160.0, heart_rate_bpm=145.0, noise_level=0.05),
    # heart_rate_bpm выше, чем у `walk`, несмотря на низкую каденцию шагов —
    # `recovery` моделирует период сразу после нагрузки, когда шаг уже
    # замедлился, а пульс остаётся повышенным и снижается с задержкой.
    "recovery": Segment(duration_s=60.0, steps_per_minute=20.0, heart_rate_bpm=110.0, noise_level=0.04),
}


def resolve_scenario(name: str) -> Segment:
    """Возвращает `Segment` встроенного сценария по имени.

    Поднимает `ValueError` с понятным сообщением, если `name` не входит в
    `SCENARIOS` — в реальном применении (PI-02/PI-03) это означает, что
    `SCENARIO` указывает на префикс CSV-записи, и соответствующий код должен
    обратиться к `device/virtual/csv_player.py`, а не считать это ошибкой
    данного модуля.
    """
    try:
        return SCENARIOS[name]
    except KeyError:
        raise ValueError(
            f"Неизвестный встроенный сценарий {name!r}; ожидается один из "
            f"{sorted(SCENARIOS)} либо префикс CSV-записи "
            "(см. device/virtual/csv_player.py)"
        ) from None
