---
id: WKT-04
title: "[Тренировки] История тренировок"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-C3]
---
## Что сделать
Список прошлых тренировок, новые сверху.

## Детали / спецификация
- `GET /workouts/history` → `{items: Session[], total}`; `GET /workouts/sessions/{id}`.

## Критерии готовности
- [x] Ответ — объект, а не массив (контракт Android)

## Зависимости
- [WKT-03](WKT-03.md) — [Тренировки] Старт и завершение сессии → WorkoutCompleted

## Вопросы
Нет открытых вопросов.
