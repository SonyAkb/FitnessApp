---
id: AND-05
title: "[Устройства] Android: экран Live watch — WS и запасной REST"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 3
related_us: [US-H1]
---
## Что сделать
Живые пульс и шаги с переходом на опрос REST при обрыве WS.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ws/TelemetryWebSocket.java`, `ui/telemetry/TelemetryFragment.java`: регистрация устройства, «Simulate beat», история, статус соединения.

## Критерии готовности
- [x] Обрыв WS → опрос `GET /telemetry/latest` раз в 5 с (сценарий M-06)

## Зависимости
- [AND-01](AND-01.md) — [Android] Каркас приложения: Retrofit, сессия, навигация
- [DEV-03](DEV-03.md) — [Устройства] WebSocket живой телеметрии

## Вопросы
Нет открытых вопросов.
