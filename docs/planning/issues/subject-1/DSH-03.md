---
id: DSH-03
title: "[Дашборд] API календаря активности"
assignee: Ananasic07
labels: [subject-1, module:dashboard, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-E2]
---
## Что сделать
Дни месяца с тренировками и пропусками.

## Детали / спецификация
- `GET /api/v1/dashboard/calendar?month=2026-11` → `[{date, completed, missed, sessions:[{id, plan_name, duration_seconds}]}]`.

## Критерии готовности
- [ ] Тест за месяц с тренировками и пропусками

## Зависимости
- [DSH-02](DSH-02.md) — [Дашборд] Период неделя/месяц, шаги за 7 дней, тренировки по дням

## Вопросы
Нет открытых вопросов.
