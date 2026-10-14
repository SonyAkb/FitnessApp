---
id: ACC-04
title: "[Аккаунт] Refresh-токен и проверка типа токена"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:bug, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-A1]
---
## Что сделать
Исправить дефект Д-2 (refresh принимался как access) и добавить обновление токенов.

## Детали / спецификация
- `core/security.decode_token(token, expected_type)`; защищённые методы и WS принимают только `typ=access`.
- `POST /api/v1/auth/refresh` `{refresh_token}` → новые токены; `401` для access-токена или просроченного.
- Пароль: буквы и цифры; вес 30–300 кг (Д-8).

## Критерии готовности
- [x] Тесты `test_auth.py` (refresh, тип токена, просроченный токен, валидация)

## Зависимости
- [CORE-03](CORE-03.md) — [Core] JWT и хеширование паролей

## Вопросы
Нет открытых вопросов.
