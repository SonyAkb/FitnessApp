---
id: WKT-09
title: "[Тренировки] Убрать начисление XP из модуля тренировок"
assignee: Hupubu
labels: [subject-1, module:workouts, type:tech, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 2
related_us: [US-D1]
---
## Что сделать
Сейчас `xp_awarded = 25` захардкожено в `workouts/service.py` (нарушение N-4). XP должен решать модуль питомца (D-07).

## Детали / спецификация
- Обработчик питомца возвращает начисленное XP через payload события (`payload['xp_awarded']` заполняет pet) или публичную функцию `pet.service.xp_for_workout`.
- `workouts` сохраняет полученное значение в `xp_awarded`.

## Критерии готовности
- [ ] В `workouts` нет констант XP
- [ ] AC-G8 (Σ xp_awarded = pet.xp) покрыт тестом

## Зависимости
- [PET-05](PET-05.md) — [Питомец] Правила XP: бонус серии, порог level×100, максимум 50

## Вопросы
Нет открытых вопросов.
