---
id: AND-09
title: "[Устройства] Android: подключение узла Raspberry Pi и индикация источника"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-5]
milestone: "Sprint 5"
status: done
story_points: 2
related_us: [US-H1]
---
## Что сделать
Кнопка «Подключить устройство» (kind=raspberry_pi) показывает `device_id` и `device_token` для `.env` узла; экран показывает источник точки.

## Детали / спецификация
- Метка «Симулятор» / «Raspberry Pi» по полю `source`.

## Критерии готовности
- [x] Ручной сценарий подключения Pi в `docs/TESTING.md`

## Зависимости
- [DEV-05](DEV-05.md) — [Устройства] Приём телеметрии от Raspberry Pi: POST /telemetry/ingest

## Вопросы
Нет открытых вопросов.
