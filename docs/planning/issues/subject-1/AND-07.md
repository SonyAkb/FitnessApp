---
id: AND-07
title: "[Android] Unit-тесты: валидация форм, DTO, настроение"
assignee: MouseViolin
labels: [subject-1, module:android, type:test, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 2
related_us: [US-A1, US-H1]
---
## Что сделать
JUnit-тесты бизнес-логики без эмулятора.

## Детали / спецификация
- `AuthValidator` вынесен из `AuthActivity`; тесты `AuthValidatorTest`, `DtoParsingTest`, `UiFormatTest` в `mobile-fit-baddy/app/src/test/`.

## Критерии готовности
- [x] `./gradlew testDebugUnitTest` зелёный в CI

## Зависимости
- [AND-06](AND-06.md) — [Аккаунт] Android: Splash, вход/регистрация, профиль и выход

## Вопросы
Нет открытых вопросов.
