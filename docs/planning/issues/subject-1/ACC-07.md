---
id: ACC-07
title: "[Аккаунт] Android: обновление токена при 401"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:auth, type:feature, sprint-6]
milestone: "Sprint 6"
status: todo
story_points: 2
related_us: [US-A1]
---
## Что сделать
При 401 приложение один раз пробует `POST /auth/refresh` и повторяет запрос; при неудаче — экран входа.

## Детали / спецификация
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/api/AuthInterceptor.java` → OkHttp `Authenticator`; хранить refresh-токен в `SessionStore`.

## Критерии готовности
- [ ] Unit-тест логики повтора
- [ ] Ручной сценарий: просроченный access не выкидывает пользователя

## Зависимости
- [ACC-04](ACC-04.md) — [Аккаунт] Refresh-токен и проверка типа токена

## Вопросы
Нет открытых вопросов.
