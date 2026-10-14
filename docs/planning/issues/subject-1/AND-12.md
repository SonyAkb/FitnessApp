---
id: AND-12
title: "[Тренировки] Android: таймер отдыха"
assignee: Hupubu
labels: [subject-1, module:workouts, type:feature, sprint-5]
milestone: "Sprint 5"
status: todo
story_points: 3
related_us: [US-C1]
---
## Что сделать
Таймер отдыха 30/60/90/120 с, «Пропустить», «+30 с», «Пауза», вибрация в конце.

## Детали / спецификация
- Логика в чистом Java-классе `mobile-fit-baddy/app/src/main/java/com/fitquest/app/workout/RestTimer.java` с внедряемыми часами (для unit-тестов); UI только подписывается.

## Критерии готовности
- [ ] `RestTimerTest`: старт, +30, пауза, окончание
- [ ] Вибрация по окончании

## Зависимости
Нет.

## Вопросы
Нет открытых вопросов.
