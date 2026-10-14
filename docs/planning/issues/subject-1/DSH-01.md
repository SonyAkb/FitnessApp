---
id: DSH-01
title: "[Дашборд] Недельная сводка"
assignee: Ananasic07
labels: [subject-1, module:dashboard, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-E1]
---
## Что сделать
Агрегированная сводка для главного экрана и экрана прогресса.

## Детали / спецификация
- `backend-fit-baddy/app/modules/dashboard/service.py` читает публичные функции `pet`, `workouts`, `auth`, `devices` (D-06), ничего не хранит.
- `GET /api/v1/dashboard/summary`.

## Критерии готовности
- [x] Стрик и XP совпадают с `/pet` (тест)

## Зависимости
- [PET-03](PET-03.md) — [Питомец] GET /pet
- [WKT-03](WKT-03.md) — [Тренировки] Старт и завершение сессии → WorkoutCompleted

## Вопросы
Нет открытых вопросов.
