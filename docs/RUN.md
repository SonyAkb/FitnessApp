# Запуск MVP FitQuest

Текущий срез: **FastAPI-мост + PostgreSQL + Android Java**. Raspberry Pi не поднимается. Основной клиент — не React.

Подробный контракт: `docs/API_CONTRACT.md`. Сценарии: `docs/USER_STORIES.md`.

---

## 1. Backend и база: Docker Compose

Из корня репозитория:

```bash
docker compose up --build
```

Ожидаемый результат этого шага: **PostgreSQL** и **FastAPI** (порт `8000`).

- Целевой код моста — папка `backend-fit-baddy/` (её ведёт агент/владелец backend).
- Файл `docker-compose.yml` в корне общий: его правят параллельно. Если сервис всё ещё собирается из исторического `./backend`, для демо моста используйте тот сервис, который слушает `:8000` и отдаёт `/api/v1` + Swagger.
- Сервис `frontend` (React/Vite на `:5173`), если он есть в compose, **не обязателен** для MVP. Это старая заглушка.

Проверка API:

```bash
curl http://localhost:8000/docs
# или
curl http://localhost:8000/health
```

Остановка: `Ctrl+C` или `docker compose down`. Том Postgres сохраняет данные между запусками.

Переменные окружения — в `.env` (не коммитить). Ориентир, без секретов:

```
POSTGRES_USER=fitquest
POSTGRES_PASSWORD=fitquest
POSTGRES_DB=fitquest
```

JWT-секрет и mock-подпись webhook задаются окружением backend, не хардкодом в git.

---

## 2. Android: Android Studio

1. Откройте папку **`mobile-fit-baddy/`** как проект в Android Studio (не весь монорепозиторий, если Studio просит корень модуля).
2. Дождитесь Gradle Sync.
3. Запустите на эмуляторе (API уровня, который указан в модуле).

Приложение — основной UI: регистрация, тренировка, питомец, дашборд, телеметрия, mock Pro.

---

## 3. Base URL эмулятора

Эмулятор Android **не** видит `localhost` хоста как себя. Базовый URL API:

```
http://10.0.2.2:8000
```

`10.0.2.2` — адрес машины, где крутится Docker, с точки зрения эмулятора.

| Где запущено приложение | Base URL |
|---|---|
| Эмулятор Android | `http://10.0.2.2:8000` |
| Браузер / curl на том же ПК | `http://localhost:8000` |
| Физический телефон в той же Wi-Fi | `http://<LAN-IP-ПК>:8000` (cleartext HTTP должен быть разрешён в манифесте/network security config) |

Префикс методов: `/api/v1/...`. Пример логина: `POST http://10.0.2.2:8000/api/v1/auth/login`.

Если Studio и Docker на одной машине, порт `8000` не должен быть занят другим процессом.

---

## 4. Swagger

После шага 1 откройте в браузере:

[http://localhost:8000/docs](http://localhost:8000/docs)

Там же можно выписать JWT и прогнать сценарий без телефона: register → login → plan → session → complete → pet → dashboard.

ReDoc, если включён: `http://localhost:8000/redoc`.

---

## Что не является основным клиентом

Папка **`frontend/`** — React-заглушка раннего каркаса. Её можно собрать для справки, но:

- демонстрация MVP идёт через **Android**;
- пользовательские истории в `docs/USER_STORIES.md` описывают Android ↔ FastAPI;
- не нужно поднимать Vite, чтобы считать проект «запущенным».

---

## Что не запускать в этом срезе

- **`pi-fit-baddy`** — папка-план под Raspberry Pi, железа в MVP нет. Телеметрия: `POST /api/v1/telemetry/simulate` и WS.
- **Stripe CLI / боевые ключи** — не требуются. Оплата: mock `POST /api/v1/subscription/checkout` и идемпотентный mock-webhook.
- Локальная установка PostgreSQL, Python, Node «вручную» для стандартного пути не нужна: инфраструктура — Docker.

---

## Минимальный смоук после старта

1. Swagger открывается.
2. `POST /api/v1/auth/register` создаёт пользователя.
3. Эмулятор логинится на `10.0.2.2:8000`.
4. Старт и complete сессии меняют `GET /api/v1/pet`.
5. `POST /api/v1/telemetry/simulate` даёт точку; экран пульса/шагов показывает её или «последнее известное».
