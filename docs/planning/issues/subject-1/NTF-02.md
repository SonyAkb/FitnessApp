---
id: NTF-02
title: "[Уведомления] API списка и отметки прочтения"
assignee: Ananasic07
labels: [subject-1, module:notifications, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-F2]
---
## Что сделать
Центр уведомлений.

## Детали / спецификация
- `GET /api/v1/notifications` (новые сверху), `POST /notifications/{id}/read`.

## Критерии готовности
- [x] Чужое уведомление → 404

## Зависимости
- [NTF-01](NTF-01.md) — [Уведомления] Модель уведомлений и обработчики событий

## Вопросы
Нет открытых вопросов.
