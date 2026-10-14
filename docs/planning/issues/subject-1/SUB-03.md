---
id: SUB-03
title: "[Подписка] Лимит Free: не больше 2 программ"
assignee: MouseViolin
labels: [subject-1, module:subscription, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 2
related_us: [US-G1]
---
## Что сделать
Entitlement `plans_unlimited` у Pro; на Free третья программа не создаётся.

## Детали / спецификация
- `POST /workouts/plans` на Free при 2 программах → `403 {detail: "Нужна подписка Pro"}` через `subscription.service.can_use` (разрешённый вызов, ARCHITECTURE §5).
- `GET /subscription` отдаёт таблицу функций и цену для экрана тарифов.

## Критерии готовности
- [ ] Тест лимита
- [ ] Контракт в `docs/API_CONTRACT.md`

## Зависимости
- [SUB-02](SUB-02.md) — [Подписка] Подпись webhook, PaymentProvider и проверка доступа can_use

## Вопросы
Цена Pro для демо?
