---
id: NTF-03
title: "[Уведомления] Фильтр непрочитанных, лимит и тесты"
assignee: Ananasic07
labels: [subject-1, module:notifications, type:test, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-F2]
---
## Что сделать
Закрыть AC9.4 и AC9.8, покрыть модуль тестами.

## Детали / спецификация
- `GET /notifications?unread_only=true&limit=50`.
- `tests/test_notifications.py`.

## Критерии готовности
- [x] Тесты зелёные

## Зависимости
- [NTF-02](NTF-02.md) — [Уведомления] API списка и отметки прочтения

## Вопросы
Нет открытых вопросов.
