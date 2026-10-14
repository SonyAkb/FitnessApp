---
id: ACC-03
title: "[Аккаунт] Обновление профиля: цель, вес, уровень"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:profile, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-A2]
---
## Что сделать
Частичное обновление профиля без затирания незаданных полей.

## Детали / спецификация
- `PATCH /api/v1/profile` `{display_name?, goal?, weight_kg?, fitness_level?}` → `MeOut`; `exclude_unset=True`.

## Критерии готовности
- [x] Поле, не переданное в запросе, не обнуляется

## Зависимости
- [ACC-01](ACC-01.md) — [Аккаунт] Модели User и Profile, регистрация

## Вопросы
Нет открытых вопросов.
