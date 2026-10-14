---
id: AND-08
title: "[Устройства] Android: офлайн-кэш последней точки и статус с датой"
assignee: MouseViolin
labels: [subject-1, module:devices, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 2
related_us: [US-H1]
---
## Что сделать
Закрыть AC12.5–12.6: если недоступен и WS, и REST — показать последнюю сохранённую точку с временем.

## Детали / спецификация
- Кэш последней `TelemetryDto` в `SharedPreferences` (JSON); статус «офлайн, последнее известное · 14:32».
- Логика выбора источника — чистый класс `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ws/TelemetrySourcePolicy.java` с unit-тестом.

## Критерии готовности
- [ ] `TelemetrySourcePolicyTest`
- [ ] Сценарий M-06 расширен

## Зависимости
- [AND-05](AND-05.md) — [Устройства] Android: экран Live watch — WS и запасной REST

## Вопросы
Нет открытых вопросов.
