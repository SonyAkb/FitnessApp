---
id: PET-01
title: "[Питомец] Модель питомца и создание при регистрации"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-D1]
---
## Что сделать
Питомец пользователя с XP, уровнем, энергией, настроением и серией.

## Детали / спецификация
- `backend-fit-baddy/app/modules/pet/models.py`: `pets` (xp, level, energy 0..100, mood, streak_days, last_activity_date).
- Обработчик `user_registered` → питомец `FitBuddy`, уровень 1.

## Критерии готовности
- [x] Питомец создаётся при регистрации (тест)

## Зависимости
- [CORE-02](CORE-02.md) — [Core] Шина событий внутри процесса
- [ACC-01](ACC-01.md) — [Аккаунт] Модели User и Profile, регистрация

## Вопросы
Нет открытых вопросов.
