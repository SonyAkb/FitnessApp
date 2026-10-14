---
id: WKT-01
title: "[Тренировки] Модели планов, упражнений плана и сессий"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-B1, US-C2]
---
## Что сделать
Хранение программ тренировок и фактических сессий.

## Детали / спецификация
- `backend-fit-baddy/app/modules/workouts/models.py`: `workout_plans`, `workout_plan_exercises` (name, sets, reps, weight_kg, rest_seconds, order_index), `workout_sessions` (status in_progress|completed, started_at, completed_at, duration_seconds, xp_awarded, scheduled_id).

## Критерии готовности
- [x] Схема совпадает с `docs/DATABASE.md`

## Зависимости
- [CORE-01](CORE-01.md) — [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose

## Вопросы
Нет открытых вопросов.
