# FitQuest Backend (`backend-fit-baddy`)

Сервер-мост проекта FitQuest: REST API `/api/v1` и WebSocket телеметрии для Android-клиента, приём телеметрии от симулятора и узла Raspberry Pi, хранение в PostgreSQL. Модульный монолит на FastAPI.

- Swagger: `http://localhost:8000/docs` · health: `GET /health`
- Полный контракт: [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) · архитектура: [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) · схема БД: [`docs/DATABASE.md`](../docs/DATABASE.md)

> Папка самодостаточна: всё, что нужно для запуска и тестов, лежит здесь. Ссылки на `../docs` — справочные; при выносе в отдельный репозиторий их заменяют копией документов.

## Быстрый старт

### Docker (рекомендуется)

Из корня монорепозитория:

```bash
cp .env.example .env
docker compose up --build            # сервисы db (PostgreSQL 16) и backend (:8000)
```

Только эта папка, без корневого compose:

```bash
docker build -t fitquest-backend .
docker run --rm -p 8000:8000 -e DATABASE_URL=sqlite:///./dev.sqlite fitquest-backend
```

### Локально (Python 3.11)

```bash
python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./dev.sqlite uvicorn app.main:app --reload
```

На Python 3.13+ закреплённые версии `pydantic-core` и `psycopg2-binary` не собираются — используйте 3.11.

## Конфигурация

Все настройки — переменные окружения (`app/core/config.py`), секреты в git не хранятся.

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://fitquest:fitquest@db:5432/fitquest` | строка подключения SQLAlchemy |
| `SECRET_KEY` | `CHANGE_ME_dev_only_secret` | ключ подписи JWT — **заменить** вне локальной разработки |
| `ALGORITHM` | `HS256` | алгоритм JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | время жизни access-токена |
| `MOCK_WEBHOOK_SECRET` | `dev-mock-webhook-secret` | ожидаемое значение `X-Mock-Signature` sandbox-webhook |
| `TELEMETRY_WS_INTERVAL_SECONDS` | `5.0` | период WS-телеметрии |
| `CORS_ORIGINS` | `*` | разрешённые origin через запятую |
| `ENV`, `APP_NAME` | `dev`, `FitQuest API` | служебные |

## Структура

```
app/
  main.py              сборка приложения, подключение роутеров, lifespan
  events.py            шина событий в процессе (publish/subscribe)
  core/                config, database, security (JWT, bcrypt), deps, clock
  modules/
    auth/              пользователи, профиль, расписание        — модуль 1
    workouts/          программы, сессии, история               — модуль 2
    pet/               питомец: XP, уровень, настроение, серия  — модуль 3
    dashboard/         сводка (агрегирует данные модулей)       — модуль 4
    notifications/     центр уведомлений, обработчики событий   — модуль 4
    devices/           устройства, телеметрия, симулятор, WS    — модуль 5
    ai/                рекомендации (правила), история          — модуль 5
    subscription/      Free/Pro, sandbox checkout, webhook      — модуль 5
tests/                 pytest: API-тесты через TestClient
```

Каждый модуль: `router.py` (HTTP) → `schemas.py` (Pydantic) → `service.py` (логика) → `models.py` (SQLAlchemy). Модули не импортируют чужие модели; реакции на действия других модулей идут через события (`app/events.py`). Разрешённые межмодульные вызовы перечислены в `docs/ARCHITECTURE.md`, раздел 5.

## Эндпоинты

| Модуль | Метод и путь |
|---|---|
| auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`, `PATCH /profile` |
| schedule | `GET/POST /schedule`, `PATCH/DELETE /schedule/{id}`, `POST /schedule/{id}/miss` |
| workouts | `GET/POST /workouts/plans`, `GET /workouts/plans/{id}`, `POST /workouts/sessions`, `GET /workouts/sessions/{id}`, `POST /workouts/sessions/{id}/complete`, `GET /workouts/history` |
| pet | `GET /pet` |
| dashboard | `GET /dashboard/summary` |
| notifications | `GET /notifications`, `POST /notifications/{id}/read` |
| devices | `POST /devices/register`, `GET /telemetry/latest`, `GET /telemetry/history`, `POST /telemetry/simulate`, `WS /telemetry/ws` |
| ai | `GET /ai/recommend`, `GET /ai/history` |
| subscription | `GET /subscription`, `POST /subscription/checkout`, `POST /subscription/webhook` |

Все пути — с префиксом `/api/v1`. Защищённые методы ждут `Authorization: Bearer <access_token>`. WebSocket: `ws://host:8000/api/v1/telemetry/ws?token=<jwt>` или первым сообщением `{"token": "<jwt>"}`.

Запланировано (см. `docs/planning/issues/`): `POST /telemetry/ingest` (приём от Raspberry Pi по `X-Device-Token`), квесты и достижения питомца, каталог упражнений и подходы.

## События

| Событие | Кто публикует | Кто слушает |
|---|---|---|
| `user_registered` | auth | pet (создать питомца), subscription (тариф Free) |
| `workout_completed` | workouts | pet (+XP, настроение, серия), notifications |
| `workout_missed` | schedule (auth) | pet (−энергия), notifications |
| `pet_leveled_up` | pet | notifications |

## Демо-сценарий через API

1. `POST /api/v1/auth/register`
2. `POST /api/v1/workouts/plans`
3. `POST /api/v1/workouts/sessions`
4. `POST /api/v1/workouts/sessions/{id}/complete` → событие `workout_completed`
5. `GET /api/v1/pet` — XP вырос, настроение `happy`
6. `GET /api/v1/dashboard/summary`, `GET /api/v1/notifications`
7. `POST /api/v1/telemetry/simulate` → `GET /api/v1/telemetry/latest`

## Тесты

```bash
pytest                       # SQLite в памяти, Docker не нужен
```

Тесты — `tests/test_api.py` (сквозные сценарии через `TestClient`). Стратегия, запуск на PostgreSQL и CI — [`docs/TESTING.md`](../docs/TESTING.md).

## База данных

Сейчас таблицы создаются при старте (`Base.metadata.create_all`). Переход на Alembic-миграции запланирован. Если схема поменялась, а данные не нужны: `docker compose down -v && docker compose up --build`.

## Владельцы

| Модуль | Предмет 1 | Предмет 2 |
|---|---|---|
| auth, schedule | @NastyaZhilinaRis2 | @Hupubu (backend) |
| workouts | @Hupubu | @Hupubu |
| pet | @SonyAkb | @Hupubu |
| dashboard, notifications | @Ananasic07 | @Hupubu |
| devices, ai, subscription | @MouseViolin | @Hupubu |
