---
id: AND-01
title: "[Android] Каркас приложения: Retrofit, сессия, навигация"
assignee: MouseViolin
labels: [subject-1, module:android, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 5
related_us: [US-A1]
---
## Что сделать
Gradle-проект Android на Java с клиентом API и нижней навигацией.

## Детали / спецификация
- `mobile-fit-baddy/` (SDK 34, min 26, Java 17), `mobile-fit-baddy/app/src/main/java/com/fitquest/app/api/` (Retrofit, `AuthInterceptor`, DTO), `auth/SessionStore.java` (EncryptedSharedPreferences), `ui/MainActivity.java` (Den/Quest/Trail/Calls/Pack).

## Критерии готовности
- [x] `./gradlew assembleDebug` собирается
- [x] Адрес API меняется без пересборки

## Зависимости
Нет.

## Вопросы
Нет открытых вопросов.
