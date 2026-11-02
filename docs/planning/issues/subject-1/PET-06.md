---
id: PET-06
title: "[Питомец] Настроение по дням без тренировки, сон и бонус возвращения"
assignee: SonyAkb
labels: [subject-1, module:pet, type:feature, sprint-4]
milestone: "Sprint 4"
status: done
story_points: 3
related_us: [US-D2]
---
## Что сделать
Настроение: 1–2 дня → neutral, 3–13 → sad, 14+ → sleeping; возвращение — приветствие и бонус XP (D-14).

## Детали / спецификация
- Считать при `GET /pet` и в ежедневной проверке от `last_activity_date` (без фоновых задач — при запросе).
- Возвращение после 3+ дней: `+10 XP`, событие `pet_returned` → уведомление «Рад тебя видеть!».
- Android: картинка для `sleeping`.

## Критерии готовности
- [x] Тесты с управляемыми часами на каждый порог (`tests/test_pet_mood.py`: 1/2 → neutral, 3/13 → sad, 14+ → sleeping; `frozen_clock` — monkeypatch `utc_now`)
- [x] Событие возвращения (`pet_returned` → уведомление «Рад тебя видеть!», +10 XP)

## Зависимости
- [PET-05](PET-05.md) — [Питомец] Правила XP: бонус серии, порог level×100, максимум 50

## Вопросы
Нет открытых вопросов.
