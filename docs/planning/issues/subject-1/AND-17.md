---
id: AND-17
title: "[Уведомления] Android: локальные напоминания о тренировке"
assignee: Ananasic07
labels: [subject-1, module:notifications, type:feature, sprint-6]
milestone: "Sprint 6"
status: todo
story_points: 3
related_us: [US-F1]
---
## Что сделать
Напоминание за выбранное время (1 ч / 30 / 15 / 5 мин) без FCM (D-16).

## Детали / спецификация
- `WorkManager`/`AlarmManager` по расписанию из `GET /schedule`; настройки — на экране профиля; канал уведомлений Android 8+; разрешение `POST_NOTIFICATIONS` (Android 13+).

## Критерии готовности
- [ ] Ручной сценарий: напоминание приходит в срок
- [ ] Отключение работает

## Зависимости
- [AND-18](AND-18.md) — [Расписание] Android: экран расписания на неделю

## Вопросы
Нет открытых вопросов.
