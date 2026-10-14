---
id: ACC-02
title: "[Аккаунт] Вход и выдача JWT"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-A1]
---
## Что сделать
Вход по email и паролю. **Опорная задача для оценки (2 SP).**

## Детали / спецификация
- `POST /api/v1/auth/login` `{email, password}` → `200` токены + `user`; `401 Invalid email or password`.
- `GET /api/v1/auth/me` — текущий пользователь с профилем.

## Критерии готовности
- [x] Неверный пароль → 401 без уточнения, что именно неверно
- [x] Тест входа

## Зависимости
- [ACC-01](ACC-01.md) — [Аккаунт] Модели User и Profile, регистрация

## Вопросы
Нет открытых вопросов.
