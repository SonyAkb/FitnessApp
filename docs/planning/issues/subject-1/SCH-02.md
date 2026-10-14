---
id: SCH-02
title: "[Расписание] Запрет слотов в прошлом и фильтр по датам"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:schedule, type:bug, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-B2]
---
## Что сделать
Исправить AC3.3 (слот в прошлом принимался) и AC2.3 (`from/to` игнорировались).

## Детали / спецификация
- `auth/schemas._require_not_past` с допуском 15 мин (D-25) для создания и изменения.
- `GET /schedule?from=&to=`.

## Критерии готовности
- [x] Тесты `test_schedule.py`

## Зависимости
- [SCH-01](SCH-01.md) — [Расписание] CRUD слотов и отметка пропуска → WorkoutMissed

## Вопросы
Нет открытых вопросов.
