# FitQuest Raspberry Pi (`pi-fit-baddy`)

Узел датчиков FitQuest: Raspberry Pi с акселерометром **MPU6050** (шаги) и пульсометром **MAX30102** (пульс) на шине I2C. Сервис считает шаги и пульс, отдаёт их по локальному API `/device/*` и публикует в backend FitQuest как `TelemetryDTO` с `source=raspberry_pi`.

> **Статус: в разработке.** Код ещё не написан; этот README описывает целевое устройство модуля по требованиям [`docs/pi.md`](../docs/pi.md) и решениям D-08, D-17, D-18 ([`docs/planning/DECISIONS.md`](../docs/planning/DECISIONS.md)). Задачи — `docs/planning/issues/` (префикс `PI-`).
>
> Папка самодостаточна (свой `requirements.txt`, тесты, CI-job).

Главное правило: **код, проверенный на Mac/Linux в эмуляции, без изменений работает на плате.** При переезде меняются только переменные окружения.

## Как устроено

```
device/
  api/         FastAPI: /device/status, /device/vitals/current, /device/vitals/history, WS /device/stream
  services/    step_counter.py, heart_rate.py, sampler.py (фоновый опрос + кольцевой буфер), publisher.py
  drivers/     mpu6050.py, max30102.py — работают с любой шиной, об эмуляции не знают
  bus/         factory.py (единственное ветвление по SENSOR_MODE), fake_smbus.py
  virtual/     VirtualMPU6050, VirtualMax30102 (карты регистров), signals.py, scenarios.py, CSV-проигрыватель
  tests/
  data/        записи с реальных датчиков (CSV)
```

```mermaid
flowchart TB
  API["api — /device/*"] --> SVC["services — шаги, пульс, sampler"]
  PUB["services/publisher.py"] --> SVC
  SVC --> DRV["drivers — Mpu6050, Max30102"]
  DRV --> BUS["bus/factory.py"]
  BUS -- "SENSOR_MODE=real" --> SMB["smbus2.SMBus(I2C_BUS)"]
  BUS -- "SENSOR_MODE=mock" --> FAKE["FakeSMBus → virtual/*"]
  PUB -- "POST /api/v1/telemetry/ingest<br/>X-Device-Token" --> BE["backend-fit-baddy"]
```

- Драйверы используют только `write_byte_data`, `read_byte_data`, `read_i2c_block_data` — эти методы есть и у `smbus2.SMBus`, и у `FakeSMBus`.
- `smbus2` и `gpiozero` импортируются лениво, только в ветке `real`; на Mac модуль импортируется без них.
- Время — через внедряемые часы `Clock.now()`; в тестах часы управляемые, `time.sleep` в тестируемой логике нет.
- Виртуальные чипы ведут себя как железо: спящий MPU6050 отдаёт нули, неверный адрес → `OSError(121, "Remote I/O error")`, невычитанный FIFO MAX30102 переполняется.

## Запуск без платы (mock)

```bash
cd pi-fit-baddy
python3.11 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                           # без smbus2 / gpiozero
SENSOR_MODE=mock GPIOZERO_PIN_FACTORY=mock pytest
SENSOR_MODE=mock uvicorn device.api.main:app --port 8080
curl http://localhost:8080/device/status                   # {"connected": true, "battery": 82, "mode": "mock"}
```

Сценарий синтетики выбирается переменной `SCENARIO` (`rest`, `walk`, `run`, `recovery` или путь к CSV).

## Запуск на Raspberry Pi (real)

1. Raspberry Pi OS, Python 3.11+. Включить I2C: `sudo raspi-config` → Interface Options → I2C → Enable, перезагрузить.
2. Подключить датчики (схема ниже) и проверить адреса: `sudo apt install i2c-tools && i2cdetect -y 1` — должны появиться `68` и `57`.
3. Установить зависимости платы: `pip install -r requirements.txt -r requirements-pi.txt` (`smbus2`, `gpiozero`).
4. Запустить: `SENSOR_MODE=real uvicorn device.api.main:app --host 0.0.0.0 --port 8080`.

### Схема подключения

Оба датчика — на шину I2C1 (`I2C_BUS=1`), параллельно.

| Сигнал | Raspberry Pi (физ. пин) | MPU6050 (GY-521) | MAX30102 |
|---|---|---|---|
| 3.3 V | 1 | VCC | VIN |
| GND | 6 | GND | GND |
| SDA (GPIO2) | 3 | SDA | SDA |
| SCL (GPIO3) | 5 | SCL | SCL |
| адрес | — | `0x68` (AD0 → GND) | `0x57` |
| прерывание (необязательно) | 11 (GPIO17, `MAX30102_INT_PIN`) | — | INT |

Питание и подтяжки зависят от конкретных плат-модулей — см. «Проверить на реальной плате».

## Отправка данных в backend

1. В Android-приложении: Live watch → «Подключить устройство» (тип `raspberry_pi`) → получить `device_id` и `device_token`.
2. Записать их в `.env` узла (пример — `.env.example`):

```
BACKEND_URL=http://192.168.1.10:8000
DEVICE_ID=pi-livingroom-01
DEVICE_TOKEN=<из приложения>
PUBLISH_ENABLED=true
```

Публикатор раз в `PUBLISH_INTERVAL_SECONDS` отправляет `POST /api/v1/telemetry/ingest` с заголовком `X-Device-Token`. `user_id` узел не знает: backend определяет пользователя по токену. Калории считаются по шагам: `calories = round(steps × CALORIES_PER_STEP)`. Если backend недоступен, точки буферизуются и отправляются позже.

## Конфигурация

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `SENSOR_MODE` | `mock` | `mock` — FakeSMBus и виртуальные чипы; `real` — `smbus2` |
| `I2C_BUS` | `1` | номер шины I2C |
| `MPU6050_ADDR` / `MAX30102_ADDR` | `0x68` / `0x57` | адреса датчиков |
| `MAX30102_INT_PIN` | `17` | GPIO прерывания (если подключён) |
| `GPIOZERO_PIN_FACTORY` | — | `mock` в тестах |
| `SAMPLE_RATE_HZ`, `STEP_THRESHOLD_G`, `STEP_MIN_INTERVAL_MS`, `HR_BAND_HZ`, `HR_WINDOW_S` | в `device/config.py` | параметры алгоритмов (подбираются на железе) |
| `HISTORY_MAX_POINTS` | `3600` | размер кольцевого буфера |
| `BATTERY_PERCENT` | `82` | заряд для `/device/status` (датчика заряда может не быть) |
| `SCENARIO` | `walk` | сценарий синтетики в mock |
| `BACKEND_URL`, `DEVICE_ID`, `DEVICE_TOKEN` | — | публикация в backend |
| `PUBLISH_ENABLED`, `PUBLISH_INTERVAL_SECONDS` | `false`, `5` | публикатор |
| `CALORIES_PER_STEP` | `0.04` | оценка калорий по шагам |

## API узла (контракт из `docs/pi.md`, не меняется)

```
GET /device/status                   → {"connected": true, "battery": 82, "mode": "mock"}
GET /device/vitals/current           → {"heart_rate": 76, "steps": 4213, "timestamp": "2026-10-14T12:00:00Z"}
GET /device/vitals/history?from=&to= → [{"heart_rate": 74, "steps": 4100, "timestamp": "..."}, ...]
WS  /device/stream                   → те же поля раз в 1–2 с
```

Время — ISO-8601 UTC. Если датчик не отвечает: `connected: false`, сервис не падает. `heart_rate` = `null`, если сигнал слабый или шумный. Android к этому API не обращается — только к backend.

## Запись CSV с реальных датчиков

```bash
SENSOR_MODE=real python -m device.tools.record --seconds 120 --out data/walk_2026-10-14
# → data/walk_2026-10-14_accel.csv (t,x,y,z) и data/walk_2026-10-14_ppg.csv (t,ir,red)
SENSOR_MODE=mock SCENARIO=data/walk_2026-10-14 pytest     # прогнать алгоритмы на записи
```

## Значения из даташитов

Не придумываются. Каждое помечается в коде `TODO(datasheet)` со ссылкой на раздел даташита, пока не сверено:

- чувствительность акселерометра MPU6050 (LSB/g) для ±2/4/8/16 g и биты выбора диапазона в `ACCEL_CONFIG` (0x1C);
- `PART_ID` MAX30102 и битовые поля `MODE_CONFIG`, `SPO2_CONFIG`, `FIFO_CONFIG`, `INT_STATUS`;
- формат отсчёта FIFO (байт на канал, значимые биты, порядок каналов в режиме SpO2);
- работа указателей FIFO (32 слота, циклический буфер, поведение при переполнении).

Уже известно из `docs/pi.md`: MPU6050 — адрес `0x68`, `WHO_AM_I` (0x75) = `0x68`, после включения спит (`PWR_MGMT_1`, 0x6B), данные с `ACCEL_XOUT_H` (0x3B), 6 байт big-endian со знаком. MAX30102 — адрес `0x57`, карта регистров 0x00–0x0D, `REV_ID`/`PART_ID` = 0xFE/0xFF.

## Проверить на реальной плате

Эмуляция этого не покажет — проверяется вручную при первом подключении:

- адреса на шине (`i2cdetect -y 1`); у MPU6050 адрес меняется пином AD0 (`0x68` / `0x69`);
- питание модулей: на каких платах есть свои стабилизаторы и подтяжки SDA/SCL, не конфликтуют ли подтяжки двух модулей;
- скорость шины I2C (100/400 кГц) и стабильность чтения FIFO на ней;
- уровень шумов акселерометра в покое и при ходьбе — подобрать `STEP_THRESHOLD_G`, `STEP_MIN_INTERVAL_MS`;
- амплитуда ИК-сигнала, ток светодиодов (`LED1_PA`, `LED2_PA`), полоса фильтра и окно для пульса; порог «слабый сигнал → `null`»;
- переполнение FIFO при реальной частоте опроса;
- точность шагов и пульса против эталона (счётчик шагов телефона, пульсометр).

## Тесты

`SENSOR_MODE=mock GPIOZERO_PIN_FACTORY=mock pytest` — без платы и без `smbus2`/`RPi.GPIO`:

- MPU6050: `WHO_AM_I`; без пробуждения данных нет; смена диапазона меняет масштаб; неверный адрес → ошибка;
- MAX30102: инициализация настраивает регистры; разбор байтов FIFO; переполнение увеличивает `OVF_COUNTER`;
- шаги: «ходьба N шагов» → N ± допуск, покой → 0;
- пульс: сценарий 72 уд/мин → 72 ± 3; слабый сигнал → `null`;
- API отвечает по контракту в mock; тест переносимости — драйверы работают с подменённой шиной того же интерфейса.

## Владельцы

@MouseViolin (модуль 5, устройства).
