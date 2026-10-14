---
id: WKT-02
title: "[Тренировки] API программ тренировок"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-B1]
---
## Что сделать
Создание и чтение программ с упражнениями.

## Детали / спецификация
- `GET/POST /api/v1/workouts/plans`, `GET /workouts/plans/{id}`; принимает `title` или `name`.

## Критерии готовности
- [x] План без упражнений → `exercises: []`
- [x] Чужой план → 404

## Зависимости
- [WKT-01](WKT-01.md) — [Тренировки] Модели планов, упражнений плана и сессий

## Вопросы
Нет открытых вопросов.
