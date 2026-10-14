---
id: AND-09
title: "[Android] Подключение узла Pi и индикация источника данных"
assignee: MouseViolin
labels: [subject-2, module:android, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 2
related_us: [US-H1]
---
## Что сделать
Показать `device_token` для `.env` узла и метку «Симулятор / Raspberry Pi».

## Детали / спецификация
Спецификация из модульных задач предмета 1: [AND-09](../subject-1/AND-09.md).
- Связано с задачей `[AND-5]` из `docs/archive/TASKS_PI_BRIDGE_TEAM4_2026-09-26.md`.

## Критерии готовности
- [ ] `./gradlew testDebugUnitTest` и lint зелёные

## Зависимости
- [BE-13](BE-13.md) — [Backend] Приём телеметрии от Pi: POST /telemetry/ingest с X-Device-Token

## Вопросы
Нет открытых вопросов.
