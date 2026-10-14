---
id: SUB-04
title: "[Подписка] Android: экран тарифов Free/Pro во вкладке Pack"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:subscription, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-G1, US-G2]
---
## Что сделать
Экран сравнения тарифов с ценой, оформлением и экраном «Активирована!»; переход при попытке использовать функцию Pro.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/subscription/PlansFragment.java`, вход из Pack и из ответа 403 на ИИ/третью программу.
- Ошибка оплаты → возврат к тарифам с сообщением.

## Критерии готовности
- [ ] Ручной сценарий M-08
- [ ] Текущий тариф выделен

## Зависимости
- [SUB-03](SUB-03.md) — [Подписка] Лимит Free: не больше 2 программ

## Вопросы
Нет открытых вопросов.
