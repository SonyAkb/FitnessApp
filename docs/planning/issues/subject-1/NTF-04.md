---
id: NTF-04
title: "[Уведомления] Сообщения питомца на 2/5/7/14 день и база фраз"
assignee: Ananasic07
labels: [subject-1, module:notifications, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-D2, US-F2]
---
## Что сделать
Мотивационные сообщения при перерыве, возвращении и достижениях; возможность отключить.

## Детали / спецификация
- Проверка при входе пользователя (`GET /dashboard/summary`) — без фоновых задач: если дней без тренировки ∈ {2,5,7,14} и сообщение за этот порог ещё не создано → уведомление `kind=motivation`.
- База фраз в `notifications/phrases.py`, случайный выбор.
- `notification_settings.motivational_enabled`, `PATCH /notifications/settings`.

## Критерии готовности
- [ ] Тесты с управляемыми часами
- [ ] Отключение работает

## Зависимости
- [PET-06](PET-06.md) — [Питомец] Настроение по дням без тренировки, сон и бонус возвращения

## Вопросы
Нет открытых вопросов.
