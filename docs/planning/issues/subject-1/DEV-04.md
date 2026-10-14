---
id: DEV-04
title: "[Устройства] Валидация телеметрии, фильтр периода, защита device_id"
assignee: MouseViolin
labels: [subject-1, module:devices, type:bug, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-H1]
---
## Что сделать
Исправить Д-5 (отрицательные значения), Д-6 (чужой device_token) и AC7.7 (`from/to`).

## Детали / спецификация
- `TelemetrySimulateIn` `ge=0`; своё устройство повторно → 200, чужое → 409 (D-05); `GET /telemetry/history?from&to`.
- Тест контракта `TelemetryDTO` (simulator = raspberry_pi).

## Критерии готовности
- [x] Тесты `test_devices.py`

## Зависимости
- [DEV-02](DEV-02.md) — [Устройства] Симулятор телеметрии: simulate, latest, history

## Вопросы
Нет открытых вопросов.
