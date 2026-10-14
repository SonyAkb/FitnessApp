---
id: AND-03
title: "[Тренировки] Android: экран Quest — программы, сессия, история"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 5
related_us: [US-B1, US-C2, US-C3]
---
## Что сделать
Экран программ, запуска и завершения тренировки, истории.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/workout/WorkoutFragment.java`, `item_plan.xml`, `item_session.xml`; локальный секундомер в `SessionStore`, «Pin as today».

## Критерии готовности
- [x] Один `POST .../complete` после завершения

## Зависимости
- [AND-01](AND-01.md) — [Android] Каркас приложения: Retrofit, сессия, навигация
- [WKT-03](WKT-03.md) — [Тренировки] Старт и завершение сессии → WorkoutCompleted

## Вопросы
Нет открытых вопросов.
