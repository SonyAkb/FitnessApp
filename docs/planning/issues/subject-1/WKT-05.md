---
id: WKT-05
title: "[Тренировки] Пагинация истории и тесты модуля"
assignee: Hupubu
labels: [subject-1, module:workouts, type:test, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-C3]
---
## Что сделать
Закрыть AC8.3/8.4/8.6 и покрыть модуль тестами.

## Детали / спецификация
- `GET /workouts/history?limit=20&offset=0`; `total` — все сессии.
- `tests/test_workouts.py`.

## Критерии готовности
- [x] Тесты зелёные на SQLite и PostgreSQL

## Зависимости
- [WKT-04](WKT-04.md) — [Тренировки] История тренировок

## Вопросы
Нет открытых вопросов.
