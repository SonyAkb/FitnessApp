---
id: PET-08
title: "[Питомец] Прогресс квестов и выдача достижений по событиям"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 5
related_us: [US-D3]
---
## Что сделать
Обновлять прогресс по `workout_completed`, начислять XP, публиковать `quest_completed`/`achievement_earned`.

## Детали / спецификация
- `GET /api/v1/pet/quests` → текущие квесты с прогрессом и сроком; `GET /api/v1/pet/achievements` → полученные с датой.
- Сброс daily/weekly по периоду.

## Критерии готовности
- [ ] Тесты на каждый квест и достижение
- [ ] Уведомление о завершении квеста

## Зависимости
- [PET-07](PET-07.md) — [Питомец] Модели квестов и достижений с начальным набором

## Вопросы
Нет открытых вопросов.
