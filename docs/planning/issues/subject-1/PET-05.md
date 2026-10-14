---
id: PET-05
title: "[Питомец] Правила XP: бонус серии, порог level×100, максимум 50"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 2
related_us: [US-D1]
---
## Что сделать
Привести расчёт к решению D-13.

## Детали / спецификация
- `XP_PER_WORKOUT = 25`; бонус `+5 × (streak_days − 1)`; накопительный порог уровня n → n+1 = `n × 100`; `MAX_LEVEL = 50`.
- `xp_to_next_level` по новой формуле; функция `xp_for_workout(pet, completed_at)` — публичная (для WKT-09).

## Критерии готовности
- [ ] Тесты: бонус серии, порог, потолок 50
- [ ] `docs/API_CONTRACT.md` → Pet совпадает

## Зависимости
- [PET-04](PET-04.md) — [Питомец] Тесты правил питомца

## Вопросы
Нет открытых вопросов.
