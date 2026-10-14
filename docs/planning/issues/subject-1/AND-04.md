---
id: AND-04
title: "[Дашборд] Android: экраны Trail (прогресс) и Calls (уведомления)"
assignee: Ananasic07
labels: [subject-1, module:dashboard, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 3
related_us: [US-E1, US-F2]
---
## Что сделать
Экран прогресса со сводкой и экран уведомлений.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/progress/ProgressFragment.java`, `ui/notifications/NotificationsFragment.java`, `item_notification.xml`; нажатие — отметка прочтения.

## Критерии готовности
- [x] Сводка обновляется после тренировки

## Зависимости
- [AND-01](AND-01.md) — [Android] Каркас приложения: Retrofit, сессия, навигация
- [DSH-01](DSH-01.md) — [Дашборд] Недельная сводка
- [NTF-02](NTF-02.md) — [Уведомления] API списка и отметки прочтения

## Вопросы
Нет открытых вопросов.
