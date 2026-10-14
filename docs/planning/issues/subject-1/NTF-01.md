---
id: NTF-01
title: "[Уведомления] Модель уведомлений и обработчики событий"
assignee: Ananasic07
labels: [subject-1, module:notifications, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 3
related_us: [US-F2]
---
## Что сделать
Уведомления создаются из событий тренировок и питомца.

## Детали / спецификация
- `backend-fit-baddy/app/modules/notifications/models.py` (`notifications`: title, body, kind, is_read).
- `backend-fit-baddy/app/modules/notifications/handlers.py`: `workout_completed`, `workout_missed`, `pet_leveled_up`.

## Критерии готовности
- [x] Каждое событие создаёт уведомление (тест)

## Зависимости
- [CORE-02](CORE-02.md) — [Core] Шина событий внутри процесса

## Вопросы
Нет открытых вопросов.
