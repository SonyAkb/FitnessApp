---
id: AND-11
title: "[Android] Обновление токена при 401"
assignee: MouseViolin
labels: [subject-2, module:android, type:feature, sprint-6]
milestone: "Sprint 6"
status: todo
story_points: 2
related_us: [US-A1]
---
## Что сделать
Повтор запроса после `POST /auth/refresh`.

## Детали / спецификация
Спецификация из модульных задач предмета 1: [ACC-07](../subject-1/ACC-07.md).


## Критерии готовности
- [ ] `./gradlew testDebugUnitTest` и lint зелёные

## Зависимости
- [AND-02](AND-02.md) — [Android] Splash, вход, регистрация, профиль

## Вопросы
Нет открытых вопросов.
