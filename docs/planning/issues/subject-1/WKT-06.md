---
id: WKT-06
title: "[Тренировки] Каталог упражнений с поиском и группами мышц"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 3
related_us: [US-B1]
---
## Что сделать
Таблица `exercises`, начальный набор и поиск для конструктора программы.

## Детали / спецификация
- Таблица `exercises (id, name UK, muscle_group, description)`; сид из 30–40 упражнений (миграция данных).
- `GET /api/v1/workouts/exercises?q=&muscle_group=` — поиск без учёта регистра.
- `workout_plan_exercises.exercise_id` (nullable) — ссылка на каталог, свободный текст остаётся.

## Критерии готовности
- [ ] Тесты поиска и фильтра
- [ ] `docs/DATABASE.md` обновлён

## Зависимости
- [CORE-04](CORE-04.md) — [Core] Подключить Alembic и первую миграцию

## Вопросы
Состав начального каталога — составит владелец модуля.
