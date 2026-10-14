---
id: WKT-08
title: "[Тренировки] Фактические подходы: session exercises и sets"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 5
related_us: [US-C1, US-C2, US-E1]
---
## Что сделать
Хранить выполнение каждого подхода и отдавать его в истории.

## Детали / спецификация
- Таблицы `workout_session_exercises`, `exercise_sets` (`docs/DATABASE.md` §2); при старте сессии копируются упражнения плана.
- `POST /workouts/sessions/{id}/sets {session_exercise_id, set_index, actual_reps, actual_weight_kg, status: done|skipped}`.
- `complete` помечает неотмеченные подходы `skipped`; ответ содержит `sets_done`, `volume_kg`.

## Критерии готовности
- [ ] Тесты: отметка, пропуск, объём
- [ ] История не перезаписывается

## Зависимости
- [WKT-06](WKT-06.md) — [Тренировки] Каталог упражнений с поиском и группами мышц
- [CORE-04](CORE-04.md) — [Core] Подключить Alembic и первую миграцию

## Вопросы
Нет открытых вопросов.
