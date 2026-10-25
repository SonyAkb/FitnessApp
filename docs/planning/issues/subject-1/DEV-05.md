---
id: DEV-05
title: "[Устройства] Приём телеметрии от Raspberry Pi: POST /telemetry/ingest"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-4]
milestone: "Sprint 4"
status: done
story_points: 3
related_us: [US-H1]
---
## Что сделать
Endpoint для публикатора Pi с аутентификацией по токену устройства (D-17).

## Детали / спецификация
- `POST /api/v1/telemetry/ingest`, заголовок `X-Device-Token`; тело — `TelemetryDTO` без `user_id` (`docs/API_CONTRACT.md`).
- 401 — нет/неверный токен; 403 — `device_id` не совпадает с токеном; 422 — отрицательные значения, `heart_rate` вне 30–230.
- `user_id` берётся из `devices`.

## Критерии готовности
- [x] Тесты на все коды ответа
- [x] Точка с `source=raspberry_pi` видна в `latest`

## Зависимости
- [DEV-04](DEV-04.md) — [Устройства] Валидация телеметрии, фильтр периода, защита device_id

## Вопросы
Нет открытых вопросов.
