# Сверка драйвера MPU6050 с симулятором Wokwi

[Wokwi](https://wokwi.com) симулирует микроконтроллеры (Pi Pico, ESP32, Arduino), а не Raspberry Pi с Linux, поэтому весь узел там не запустить. Зато в нём есть независимая от нас модель **MPU6050**: на неё можно посадить **тот же файл драйвера** `device/drivers/mpu6050.py` и сравнить поведение с нашей моделью `device/virtual/mpu6050.py`. MAX30102 в Wokwi нет — его проверяем только тестами и на плате (`README.md`, «Проверить на реальной плате»).

Цепочка проверки:

```
датчик Wokwi ──I2C──► Pi Pico (MicroPython) ──► наш драйвер ──► checks.py ──► монитор порта
                                                                     └─► поток t,x,y,z ──► count_steps.py ──► наш StepCounter
наша модель (FakeSMBus + VirtualMPU6050) ──► тот же драйвер ──► тот же checks.py  (reference.py)
```

## Файлы

| Файл | Где работает | Что делает |
|---|---|---|
| `diagram.json` | Wokwi | Pi Pico + MPU6050: SDA → GP4, SCL → GP5, 3V3, GND |
| `main.py` | Wokwi | адаптер `machine.I2C` → методы `smbus2` (`read_byte_data`, `write_byte_data`, `read_i2c_block_data`), проверки, затем поток 60 с при 50 Гц |
| `checks.py` | Wokwi и у нас | 6 проверок по даташиту: WHO_AM_I, сон после включения, пробуждение, ±2g / ±8g |
| `../device/drivers/mpu6050.py` | Wokwi и узел | драйвер без изменений (в Wokwi файл называется `mpu6050.py`) |
| `reference.py` | у нас | те же проверки на нашей модели — эталон вывода |
| `count_steps.py` | у нас | шаги нашим алгоритмом по потоку из лога Wokwi |

## Запуск в браузере

1. <https://wokwi.com> → New Project → **Raspberry Pi Pico → MicroPython**.
2. Вкладка `diagram.json` — заменить содержимым `wokwi/diagram.json`.
3. `main.py` — заменить содержимым `wokwi/main.py`.
4. «+» → New file: `checks.py` (из `wokwi/checks.py`) и `mpu6050.py` (из `device/drivers/mpu6050.py`).
5. Запустить ▶. Первые строки монитора порта — проверки.

Эталон для сравнения (из `pi-fit-baddy/`): `python -m wokwi.reference`

```
CHECK who_am_i                     OK    got=0x68 expected=0x68  (регистр 0x75)
CHECK pwr_mgmt_1_on_power_up       OK    got=0x40 expected=0x40  (бит SLEEP после включения)
CHECK accel_while_asleep           OK    got=[0, 0, 0] expected=[0, 0, 0]  (спящий чип отдаёт нули)
CHECK pwr_mgmt_1_after_wake        OK    got=0x0 expected=0x0  (драйвер сбросил SLEEP)
DATA  range=±2g raw=[0, 0, 16384] g=(0.000, 0.000, 1.000)
DATA  range=±8g raw=[0, 0, 4096] g=(0.000, 0.000, 1.000)
CHECK raw_z_ratio_8g_to_2g         OK    got=0.25 expected=0.25  (4096 / 16384 LSB/g)
CHECK driver_g_same_on_both        OK    got=True expected=True  (драйвер учитывает диапазон)
RESULT 6/6 checks match the datasheet
```

`expected` — значения из даташита InvenSense (Register Map rev 4.2), а не из нашей модели. Поэтому:

- **OK в Wokwi** — независимая модель ведёт себя так же, как даташит и наша модель: драйвер и наш виртуальный чип подтверждены.
- **DIFF в Wokwi** — сначала сверить с даташитом. Документация Wokwi не обещает моделировать сон и выбор диапазона ([wokwi-mpu6050](https://docs.wokwi.com/parts/wokwi-mpu6050)): если Wokwi отдаёт данные «во сне» или не меняет масштаб на ±8g, это ограничение Wokwi, и такой пункт подтверждается только на реальной плате. Если же Wokwi расходится с даташитом там, где он его моделирует (WHO_AM_I, порядок байтов, 16384 LSB/g на ±2g), — ошибка у нас.

## Шаги: датчик Wokwi → наш алгоритм

После проверок `main.py` 60 секунд печатает поток `t,x,y,z` между `CSV-BEGIN` и `CSV-END`.

1. Во время потока кликнуть по датчику и двигать ползунок **accelZ**: 1 g → ~1.5 g → 1 g — это один «шаг». Сделать, например, 10 таких движений с паузой около полсекунды, считая их.
2. Скопировать вывод монитора порта в файл `wokwi_log.txt`.
3. Из `pi-fit-baddy/`:

```bash
python -m wokwi.count_steps wokwi_log.txt                    # «Шагов по нашему алгоритму: 10»
python -m wokwi.count_steps wokwi_log.txt --save data/wokwi_walk
SENSOR_MODE=mock SCENARIO=data/wokwi_walk uvicorn device.api.main:app --port 8080   # поток Wokwi как сценарий узла
```

Число шагов должно совпасть с числом движений ползунка. Порог и интервал берутся из тех же переменных, что у узла (`STEP_THRESHOLD_G=0.15`, `STEP_MIN_INTERVAL_MS=300`): слишком быстрые движения (чаще 300 мс) алгоритм намеренно сливает в один шаг.

## Автотесты

`device/tests/test_wokwi.py`: наша модель проходит 6/6; поток из лога разбирается и считается; `main.py` + `checks.py` + драйвер запускаются в настоящем MicroPython (если установлен: `brew install micropython`; в CI тест пропускается).

Автоматический прогон в самом Wokwi (`wokwi-cli` со сценарием `set-control` для accelZ) возможен, но требует токен Wokwi CI ([automation scenarios](https://docs.wokwi.com/wokwi-ci/automation-scenarios)) — для учебного проекта достаточно ручного прогона в браузере.
