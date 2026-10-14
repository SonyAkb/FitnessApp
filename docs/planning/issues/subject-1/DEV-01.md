---
id: DEV-01
title: "[Устройства] Регистрация устройства и модель телеметрии"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-H1]
---
## Что сделать
Хранение устройств и точек телеметрии в формате `TelemetryDTO`.

## Детали / спецификация
- `backend-fit-baddy/app/modules/devices/models.py`: `devices` (device_id UK, device_token, kind), `telemetry_points` (steps, heart_rate, calories, timestamp, source).
- `POST /api/v1/devices/register` → `{device_id, device_token, user_id, kind, status}`.

## Критерии готовности
- [x] Поля совпадают с `TelemetryDTO` из `docs/API_CONTRACT.md`

## Зависимости
- [CORE-01](CORE-01.md) — [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose

## Вопросы
Нет открытых вопросов.
