"""Считает шаги нашим StepCounter по потоку `t,x,y,z`, который Pi Pico напечатал в Wokwi.

    python -m wokwi.count_steps wokwi_log.txt               # из pi-fit-baddy/
    python -m wokwi.count_steps wokwi_log.txt --save data/wokwi_walk

Лог — скопированный вывод монитора порта Wokwi (строки между CSV-BEGIN и CSV-END).
С `--save` поток сохраняется как `<prefix>_accel.csv` для `SCENARIO=<prefix>`.
Параметры алгоритма — из окружения, как у узла (STEP_THRESHOLD_G и др.).
"""

import argparse
import sys

from device.clock import ManualClock
from device.config import load_config
from device.services.step_counter import StepCounter


def parse_stream(lines) -> list[tuple[float, float, float, float]]:
    samples, inside = [], False
    for line in lines:
        line = line.strip()
        if line.startswith("CSV-BEGIN"):
            inside, samples = True, []
            continue
        if line.startswith("CSV-END"):
            inside = False
            continue
        if inside and line:
            parts = line.split(",")
            if len(parts) == 4:
                try:
                    samples.append(tuple(float(p) for p in parts))
                except ValueError:
                    pass
    return samples


def count(samples) -> int:
    clock = ManualClock()
    counter = StepCounter.from_config(load_config(), clock)
    steps = 0
    for t, x, y, z in samples:
        clock.advance(max(t - clock.now(), 0.0))
        steps = counter.update((x, y, z))
    return steps


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="файл с выводом монитора порта Wokwi")
    ap.add_argument("--save", metavar="PREFIX", help="сохранить поток в <PREFIX>_accel.csv")
    args = ap.parse_args(argv)
    with open(args.log, encoding="utf-8") as fh:
        samples = parse_stream(fh)
    if not samples:
        print("В логе нет строк между CSV-BEGIN и CSV-END", file=sys.stderr)
        return 1
    duration = samples[-1][0] - samples[0][0]
    print(f"Отсчётов: {len(samples)} за {duration:.1f} с (~{len(samples) / max(duration, 1e-9):.0f} Гц)")
    print(f"Шагов по нашему алгоритму: {count(samples)}")
    if args.save:
        path = f"{args.save}_accel.csv"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("t,x,y,z\n")
            for t, x, y, z in samples:
                fh.write(f"{t},{x},{y},{z}\n")
        print(f"Сохранено: {path} (SCENARIO={args.save})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
