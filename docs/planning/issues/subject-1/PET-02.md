---
id: PET-02
title: "[Питомец] XP, уровень, настроение и серия по событиям"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-D1, US-D2]
---
## Что сделать
Реакция питомца на завершение и пропуск тренировки.

## Детали / спецификация
- `backend-fit-baddy/app/modules/pet/service.py`: `apply_workout_completed` (+XP, энергия, серия, уровень, mood happy|level_up, событие `pet_leveled_up`), `apply_workout_missed` (−энергия, sad, серия 0).
- `backend-fit-baddy/app/modules/pet/handlers.py`.

## Критерии готовности
- [x] Энергия в 0..100
- [x] Level-up публикует событие

## Зависимости
- [PET-01](PET-01.md) — [Питомец] Модель питомца и создание при регистрации
- [WKT-03](WKT-03.md) — [Тренировки] Старт и завершение сессии → WorkoutCompleted
- [SCH-01](SCH-01.md) — [Расписание] CRUD слотов и отметка пропуска → WorkoutMissed

## Вопросы
Нет открытых вопросов.
