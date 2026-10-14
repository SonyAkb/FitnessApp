---
id: PET-07
title: "[Питомец] Модели квестов и достижений с начальным набором"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-D3]
---
## Что сделать
Таблицы `quests`, `user_quests`, `achievements`, `user_achievements` и предустановленные записи.

## Детали / спецификация
- Квесты: «1 тренировка сегодня» (daily), «3 тренировки за неделю» (weekly).
- Достижения: `first_workout`, `three_in_row`, `week_no_miss`.
- Схема — `docs/DATABASE.md` §2.

## Критерии готовности
- [ ] Миграция Alembic
- [ ] `docs/DATABASE.md` обновлён

## Зависимости
- [CORE-04](CORE-04.md) — [Core] Подключить Alembic и первую миграцию

## Вопросы
Награды XP за каждый квест — определит владелец модуля.
