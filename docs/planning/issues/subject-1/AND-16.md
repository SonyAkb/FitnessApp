---
id: AND-16
title: "[Дашборд] Android: графики на экране прогресса"
assignee: Ananasic07
labels: [subject-1, module:dashboard, type:feature, sprint-6]
milestone: "Sprint 6"
status: todo
story_points: 3
related_us: [US-E1]
---
## Что сделать
Столбчатая диаграмма тренировок по дням и линия веса по выбранному упражнению.

## Детали / спецификация
- Простое рисование на `Canvas` или библиотека MPAndroidChart (решить в задаче).

## Критерии готовности
- [ ] Графики на данных из `workouts_by_day` и истории подходов

## Зависимости
- [DSH-02](DSH-02.md) — [Дашборд] Период неделя/месяц, шаги за 7 дней, тренировки по дням
- [WKT-08](WKT-08.md) — [Тренировки] Фактические подходы: session exercises и sets

## Вопросы
Можно ли подключить MPAndroidChart?
