---
id: WKT-03
title: "[Тренировки] Старт и завершение сессии → WorkoutCompleted"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-C2]
---
## Что сделать
Сессия тренировки и событие о её завершении.

## Детали / спецификация
- `POST /workouts/sessions {workout_plan_id|plan_id, scheduled_id?}` → 201 `in_progress`.
- `POST /workouts/sessions/{id}/complete {duration_seconds?}` → 200; повтор → 409; публикует `workout_completed {user_id, session_id, completed_at, duration_seconds}`.

## Критерии готовности
- [x] Повторное завершение → 409 (тест)
- [x] Питомец получает XP через событие

## Зависимости
- [WKT-02](WKT-02.md) — [Тренировки] API программ тренировок
- [CORE-02](CORE-02.md) — [Core] Шина событий внутри процесса

## Вопросы
Нет открытых вопросов.
