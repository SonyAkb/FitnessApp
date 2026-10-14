---
id: SUB-02
title: "[Подписка] Подпись webhook, PaymentProvider и проверка доступа can_use"
assignee: MouseViolin
labels: [subject-1, module:subscription, type:bug, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 3
related_us: [US-G2, US-H2]
---
## Что сделать
Исправить Д-1 (webhook без подписи делал Pro любому) и Д-3 (ИИ на Free).

## Детали / спецификация
- `backend-fit-baddy/app/modules/subscription/providers.py`: `PaymentProvider`, `SandboxPaymentProvider`.
- `service.can_use(db, user_id, feature)`; `ai/router` → 403 на Free.
- Webhook: `X-Mock-Signature` = `MOCK_WEBHOOK_SECRET` (`hmac.compare_digest`), `payment.failed`.

## Критерии готовности
- [x] Тесты `test_ai_subscription.py`

## Зависимости
- [SUB-01](SUB-01.md) — [Подписка] Тариф Free/Pro, mock checkout и идемпотентный webhook

## Вопросы
Нет открытых вопросов.
