---
id: CORE-03
title: "[Core] JWT и хеширование паролей"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-A1]
---
## Что сделать
Общие функции безопасности: bcrypt-хеш пароля, выпуск access/refresh JWT, зависимость `get_current_user`.

## Детали / спецификация
- `app/core/security.py`: `hash_password`, `verify_password`, `create_access_token` (`typ=access`), `create_refresh_token` (`typ=refresh`, 14 дней).
- `app/core/deps.py`: `get_current_user` — `Authorization: Bearer`, 401 с `WWW-Authenticate`.
- Секрет и алгоритм — из окружения.

## Критерии готовности
- [x] Пароль в БД хранится только как bcrypt-хеш
- [x] Защищённый метод без токена → 401

## Зависимости
- [CORE-01](CORE-01.md) — [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose

## Вопросы
Нет открытых вопросов.
