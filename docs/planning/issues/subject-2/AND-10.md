---
id: AND-10
title: "[Android] История телеметрии за период с графиком"
assignee: MouseViolin
labels: [subject-2, module:android, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-H1]
---
## Что сделать
Экран истории: выбор недели/месяца, график шагов по дням и среднего пульса.

## Детали / спецификация
- Данные — `GET /api/v1/telemetry/daily` (BE-15).
- Логика агрегации для подписей — в чистом классе с unit-тестом.

## Критерии готовности
- [ ] `./gradlew testDebugUnitTest` и lint зелёные

## Зависимости
- [BE-15](BE-15.md) — [Backend] Агрегаты телеметрии для графиков: шаги по дням, средний пульс

## Вопросы
Нет открытых вопросов.
