---
id: ACC-05
title: "[Аккаунт] Цель и уровень — фиксированные значения, онбординг профиля"
assignee: NastyaZhilinaRis2
labels: [subject-1, module:profile, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 3
related_us: [US-A2]
---
## Что сделать
Ограничить цель и уровень списками и показывать экран профиля сразу после регистрации.

## Детали / спецификация
- Backend: `goal ∈ {weight_loss, muscle_gain, endurance, health}`, `fitness_level ∈ {beginner, intermediate, advanced}`, по умолчанию `beginner`; 422 для других значений.
- Android: после регистрации — экран профиля с выпадающими списками, числовой клавиатурой для веса, кнопкой «Начать тренировки» (активна при заполненной цели) и «Пропустить» с предупреждением.
- `mobile-fit-baddy/app/src/main/java/com/fitquest/app/ui/profile/`, `res/layout/fragment_profile.xml`.

## Критерии готовности
- [ ] Неизвестная цель → 422 (тест)
- [ ] Онбординг показывается один раз
- [ ] Ручной сценарий описан в `docs/TESTING.md`

## Зависимости
- [ACC-03](ACC-03.md) — [Аккаунт] Обновление профиля: цель, вес, уровень

## Вопросы
Хранить коды на английском, а подписи — на русском в Android? (по умолчанию — да)
