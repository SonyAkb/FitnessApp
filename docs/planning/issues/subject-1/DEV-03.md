---
id: DEV-03
title: "[Устройства] WebSocket живой телеметрии"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-H1]
---
## Что сделать
Поток телеметрии для Android.

## Детали / спецификация
- `WS /api/v1/telemetry/ws?token=` или первым сообщением `{"token"}`; неверный токен → close 4401.

## Критерии готовности
- [x] Тесты WS (`test_devices.py`)

## Зависимости
- [DEV-02](DEV-02.md) — [Устройства] Симулятор телеметрии: simulate, latest, history

## Вопросы
Нет открытых вопросов.
