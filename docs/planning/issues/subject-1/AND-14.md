---
id: AND-14
title: "[Питомец] Android: анимации и реплики питомца по настроению"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-6]
milestone: "Sprint 6"
status: todo
story_points: 2
related_us: [US-D1, US-D2]
---
## Что сделать
Отдельная анимация для happy, sad, sleeping, level_up; анимация «+XP» после тренировки.

## Детали / спецификация
- `UiFormat.foxAnimationForMood`, ресурсы в `res/drawable-nodpi/`.

## Критерии готовности
- [ ] `UiFormatTest` покрывает новые настроения

## Зависимости
- [PET-06](PET-06.md) — [Питомец] Настроение по дням без тренировки, сон и бонус возвращения

## Вопросы
Готовы ли кадры для sleeping и sad?
