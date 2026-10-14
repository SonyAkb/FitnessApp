---
id: AND-02
title: "[Питомец] Android: главный экран Den с питомцем"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 5
related_us: [US-D1]
---
## Что сделать
Главный экран: питомец по настроению, уровень, XP-бар, серия, энергия, тренировка на сегодня, последние пульс и шаги.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/home/HomeFragment.java`, `ui/UiFormat.java` (настроение → картинка), кадры анимации из `Animation_1/` в `res/drawable-nodpi/`.

## Критерии готовности
- [x] Настроение сервера меняет картинку (`UiFormatTest`)

## Зависимости
- [AND-01](AND-01.md) — [Android] Каркас приложения: Retrofit, сессия, навигация
- [PET-03](PET-03.md) — [Питомец] GET /pet

## Вопросы
Нет открытых вопросов.
