---
id: AND-06
title: "[Аккаунт] Android: Splash, вход/регистрация, профиль и выход"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:feature, sprint-2]
milestone: "Sprint 2"
status: done
story_points: 3
related_us: [US-A1, US-A2]
---
## Что сделать
Экраны входа, регистрации и профиля в Android.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/SplashActivity.java` (автовход по токену), `AuthActivity.java`, `ui/profile/ProfileFragment.java` (профиль, выход, адрес API).
- Валидация формы — `auth/AuthValidator.java` (+ `AuthValidatorTest`).

## Критерии готовности
- [x] Автовход при повторном открытии
- [x] 401 → экран входа

## Зависимости
- [AND-01](AND-01.md) — [Android] Каркас приложения: Retrofit, сессия, навигация
- [ACC-02](ACC-02.md) — [Аккаунт] Вход и выдача JWT

## Вопросы
Нет открытых вопросов.
