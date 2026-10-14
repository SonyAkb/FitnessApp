---
id: SUB-01
title: "[Подписка] Тариф Free/Pro, mock checkout и идемпотентный webhook"
assignee: MouseViolin
labels: [subject-1, module:subscription, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 3
related_us: [US-G1, US-G2]
---
## Что сделать
Подписка с тестовой оплатой.

## Детали / спецификация
- `backend-fit-baddy/app/modules/subscription/models.py`: `subscriptions`, `payments`, `webhook_events` (event_id UK).
- `GET /subscription`, `POST /subscription/checkout`, `POST /subscription/webhook` (повтор → `duplicate: true`).

## Критерии готовности
- [x] Тест идемпотентности webhook

## Зависимости
- [ACC-01](ACC-01.md) — [Аккаунт] Модели User и Profile, регистрация

## Вопросы
Нет открытых вопросов.
