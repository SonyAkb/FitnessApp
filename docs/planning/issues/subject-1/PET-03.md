---
id: PET-03
title: "[Питомец] GET /pet"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 1
related_us: [US-D1]
---
## Что сделать
Отдать состояние питомца клиенту.

## Детали / спецификация
- `GET /api/v1/pet` → `{id, name, xp, xp_to_next_level, level, energy, mood, streak_days, updated_at}`.

## Критерии готовности
- [x] Нет питомца → создаётся

## Зависимости
- [PET-01](PET-01.md) — [Питомец] Модель питомца и создание при регистрации

## Вопросы
Нет открытых вопросов.
