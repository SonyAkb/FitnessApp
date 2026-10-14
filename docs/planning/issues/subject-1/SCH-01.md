---
id: SCH-01
title: "[Расписание] CRUD слотов и отметка пропуска → WorkoutMissed"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:schedule, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-B2, US-D2]
---
## Что сделать
Расписание тренировок пользователя и пропуск слота с событием.

## Детали / спецификация
- `backend-fit-baddy/app/modules/auth/models.py`: `scheduled_workouts` (planned_at, workout_plan_id, repeat_rule, status planned|missed|completed, missed_at).
- `GET/POST /schedule`, `PATCH/DELETE /schedule/{id}`, `POST /schedule/{id}/miss` → `workout_missed`; повторный miss → 409.

## Критерии готовности
- [x] Чужой слот → 404
- [x] Событие `workout_missed` доходит до питомца и уведомлений

## Зависимости
- [ACC-01](ACC-01.md) — [Аккаунт] Модели User и Profile, регистрация
- [CORE-02](CORE-02.md) — [Core] Шина событий внутри процесса

## Вопросы
Нет открытых вопросов.
