---
id: CORE-05
title: "[CI] GitHub Actions: отдельный job на backend, Android и Pi"
assignee: Ananasic07
labels: [subject-1, module:core, type:tech, sprint-3]
milestone: "Sprint 3"
status: done
story_points: 3
related_us: []
---
## Что сделать
Настроить CI, который проверяет каждую часть только при её изменении.

## Детали / спецификация
- `.github/workflows/ci.yml`: job `changes` (`dorny/paths-filter`), `backend` (Python 3.11, кэш pip, PostgreSQL 16, pytest на PostgreSQL и SQLite, ruff без блокировки), `mobile` (JDK 17, кэш Gradle, `testDebugUnitTest`, `lintDebug`, `assembleDebug`), `pi` (`SENSOR_MODE=mock`, пропуск, пока нет кода).
- Каждый job с `working-directory` своей папки, без зависимостей от соседних.

## Критерии готовности
- [x] Workflow проходит `actionlint`
- [x] Изменение только в `backend-fit-baddy/` не запускает Android-job
- [x] Все jobs зелёные на main

## Зависимости
- [WKT-05](WKT-05.md) — [Тренировки] Пагинация истории и тесты модуля
- [PET-04](PET-04.md) — [Питомец] Тесты правил питомца
- [NTF-03](NTF-03.md) — [Уведомления] Фильтр непрочитанных, лимит и тесты
- [ACC-04](ACC-04.md) — [Аккаунт] Refresh-токен и проверка типа токена

## Вопросы
Нет открытых вопросов.
