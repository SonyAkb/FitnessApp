---
id: ACC-01
title: "[Аккаунт] Модели User и Profile, регистрация"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-A1]
---
## Что сделать
Регистрация по email и паролю с созданием профиля и событием `user_registered`.

## Детали / спецификация
- `backend-fit-baddy/app/modules/auth/models.py`: `users` (email UK, hashed_password, display_name, role, is_active), `profiles` (goal, weight_kg, fitness_level).
- `POST /api/v1/auth/register` `{email, password, display_name}` → `201 {access_token, refresh_token, token_type, user}`; `409` — email занят; `422` — пароль < 8.
- Событие `user_registered` → питомец и тариф Free.

## Критерии готовности
- [x] Повторный email → 409
- [x] Пароль хешируется
- [x] Тест `test_register_and_login`

## Зависимости
- [CORE-01](CORE-01.md) — [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose
- [CORE-03](CORE-03.md) — [Core] JWT и хеширование паролей

## Вопросы
Нет открытых вопросов.
