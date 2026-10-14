---
id: DEV-02
title: "[Устройства] Симулятор телеметрии: simulate, latest, history"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-H1]
---
## Что сделать
Тестовый источник пульса и шагов.

## Детали / спецификация
- `POST /telemetry/simulate` (тело опционально) → 201 `source=simulator`; `GET /telemetry/latest` (404 без точек), `GET /telemetry/history?limit=`.

## Критерии готовности
- [x] Тест `test_telemetry_simulate_stores_a_point`

## Зависимости
- [DEV-01](DEV-01.md) — [Устройства] Регистрация устройства и модель телеметрии

## Вопросы
Нет открытых вопросов.
