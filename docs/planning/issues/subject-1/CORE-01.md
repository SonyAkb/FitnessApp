---
id: CORE-01
title: "[Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose"
assignee: MouseViolin
labels: [subject-1, module:core, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: []
---
## Что сделать
Создать скелет backend: приложение FastAPI с префиксом `/api/v1`, настройки из окружения, подключение SQLAlchemy к PostgreSQL, `docker compose up` для `db` и `backend`.

## Детали / спецификация
- `backend-fit-baddy/app/main.py` — сборка приложения, CORS, `GET /health`, подключение роутеров модулей.
- `app/core/config.py` — `pydantic-settings`: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `ENV`.
- `app/core/database.py` — `engine`, `SessionLocal`, `Base`, зависимость `get_db`; поддержка SQLite для тестов.
- `app/core/clock.py` — `utc_now()`, единая точка времени.
- `Dockerfile` (python:3.11-slim), корневой `docker-compose.yml`: `db` (postgres:16-alpine, healthcheck), `backend` (порт 8000).
- `.env.example` без секретов.

## Критерии готовности
- [x] `docker compose up --build` поднимает db и backend на Mac и Windows
- [x] `GET /health` → `{"status":"ok"}`
- [x] Swagger открывается на `/docs`

## Зависимости
Нет.

## Вопросы
Нет открытых вопросов.
