# Запуск FitQuest

Три части запускаются независимо. Контракт API — [`API_CONTRACT.md`](API_CONTRACT.md), архитектура — [`ARCHITECTURE.md`](ARCHITECTURE.md), тесты — [`TESTING.md`](TESTING.md).

| Часть | Как запустить | Что нужно установить |
|---|---|---|
| Backend + PostgreSQL | `docker compose up --build` | Docker Desktop |
| Android | Android Studio → открыть `mobile-fit-baddy/` | Android Studio (JDK 17, SDK 34) |
| Raspberry Pi (без платы) | `cd pi-fit-baddy && SENSOR_MODE=mock uvicorn device.api.main:app` (план) | Python 3.11 |

---

## 1. Backend и база (Docker Compose)

Из корня репозитория:

```bash
cp .env.example .env      # один раз; затем поменять SECRET_KEY и MOCK_WEBHOOK_SECRET
docker compose up --build
```

Поднимаются два сервиса: `db` (PostgreSQL 16, порт 5432) и `backend` (FastAPI, порт 8000). Локально ставить PostgreSQL, Python или Node не нужно.

Проверка:

```bash
curl http://localhost:8000/health
# Swagger: http://localhost:8000/docs
```

Остановка — `Ctrl+C` или `docker compose down`. Данные БД хранятся в томе `fitbaddy_pgdata`; сбросить — `docker compose down -v`.

Переменные окружения backend (секреты только в `.env`, который не коммитится):

| Переменная | Назначение |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | учётка PostgreSQL для Compose |
| `DATABASE_URL` | строка подключения SQLAlchemy (Compose задаёт сам) |
| `SECRET_KEY` | ключ подписи JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | время жизни access-токена |
| `MOCK_WEBHOOK_SECRET` | значение заголовка `X-Mock-Signature` для sandbox-webhook |
| `TELEMETRY_WS_INTERVAL_SECONDS` | период WS-телеметрии |
| `CORS_ORIGINS` | разрешённые origin (`*` для разработки) |

Backend без Docker (для разработки и тестов):

```bash
cd backend-fit-baddy
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                                                  # SQLite в памяти, Docker не нужен
DATABASE_URL=sqlite:///./dev.sqlite uvicorn app.main:app --reload
```

---

## 2. Android

1. Android Studio → **File → Open** → папка `mobile-fit-baddy/` (не корень репозитория).
2. Дождаться Gradle Sync (JDK 17).
3. Запустить конфигурацию `app` на эмуляторе API 26+.

Из командной строки:

```bash
cd mobile-fit-baddy
./gradlew assembleDebug          # сборка
./gradlew testDebugUnitTest      # unit-тесты без эмулятора
```

### Адрес backend

| Где запущено приложение | Base URL |
|---|---|
| Эмулятор Android | `http://10.0.2.2:8000` (по умолчанию) |
| Телефон в той же Wi-Fi | `http://<LAN-IP-компьютера>:8000` |
| Genymotion | `http://10.0.3.2:8000` |

Адрес меняется без пересборки: вкладка **Pack** → поле «API base URL» → «Save base URL».

---

## 3. Raspberry Pi — `pi-fit-baddy` (план)

Подробно — [`pi-fit-baddy/README.md`](../pi-fit-baddy/README.md) и требования [`pi.md`](pi.md).

```bash
cd pi-fit-baddy
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
SENSOR_MODE=mock GPIOZERO_PIN_FACTORY=mock pytest           # тесты без железа
SENSOR_MODE=mock uvicorn device.api.main:app --port 8080    # локальный API /device/*
```

Чтобы узел отправлял данные в backend:

1. В Android: Live watch → «Подключить устройство» (тип `raspberry_pi`) → получить `device_id` и `device_token`.
2. В `pi-fit-baddy/.env`: `BACKEND_URL=http://<IP-компьютера>:8000`, `DEVICE_ID=…`, `DEVICE_TOKEN=…`, `PUBLISH_ENABLED=true`.
3. На плате — то же самое с `SENSOR_MODE=real` (нужны `smbus2`, `gpiozero`, включённый I2C).

---

## 4. Смоук-проверка демо-сценария

Через Swagger (`http://localhost:8000/docs`) или Android:

1. `POST /api/v1/auth/register` — пользователь создан, питомец `level=1`.
2. `POST /api/v1/workouts/plans` → `POST /api/v1/workouts/sessions` → `POST /api/v1/workouts/sessions/{id}/complete`.
3. `GET /api/v1/pet` — XP вырос, настроение `happy`.
4. `GET /api/v1/dashboard/summary` — тренировка засчитана.
5. `GET /api/v1/notifications` — поздравление.
6. `POST /api/v1/telemetry/simulate` → экран Live watch показывает пульс и шаги.

Автоматически тот же путь проверяет тест `backend-fit-baddy/tests/test_api.py::test_full_demo_path`.
