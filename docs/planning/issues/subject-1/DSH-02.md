---
id: DSH-02
title: "[Дашборд] Период неделя/месяц, шаги за 7 дней, тренировки по дням"
assignee: Ananasic07
labels: [subject-1, module:dashboard, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 3
related_us: [US-E1]
---
## Что сделать
Сейчас `steps_7d` = последнее значение, `workouts_by_day` пуст, `period` не принимается (AC8.1–8.2).

## Детали / спецификация
- `GET /dashboard/summary?period=week|month`.
- `steps_7d` — сумма дневных максимумов шагов за 7 дней (точки телеметрии накопительные за день).
- `workouts_by_day` — массив `{date, completed}` за период (новая публичная функция `workouts.service.completed_by_day`).

## Критерии готовности
- [ ] Тесты с подготовленными данными
- [ ] Android показывает новые поля

## Зависимости
- [DSH-01](DSH-01.md) — [Дашборд] Недельная сводка

## Вопросы
Нет открытых вопросов.
