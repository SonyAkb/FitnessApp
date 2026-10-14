---
id: DEV-06
title: "[Устройства] WebSocket рассылает сохранённые точки, а не генерирует"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 3
related_us: [US-H1]
---
## Что сделать
Сейчас WS сам создаёт синтетику, поэтому данные Pi в него не попадут (П-17).

## Детали / спецификация
- После сохранения точки (`simulate`/`ingest`) — событие `telemetry_received`; WS-менеджер рассылает её подключённым клиентам этого пользователя (in-memory `dict[user_id, set[WebSocket]]`).
- Режим автосимуляции для демо: `TELEMETRY_AUTO_SIMULATE=true` — фоновая задача раз в N с вызывает `simulate`.

## Критерии готовности
- [ ] Тест: точка из ingest приходит в открытый WS
- [ ] Без автосимуляции WS молчит, пока нет точек

## Зависимости
- [DEV-05](DEV-05.md) — [Устройства] Приём телеметрии от Raspberry Pi: POST /telemetry/ingest

## Вопросы
Нет открытых вопросов.
