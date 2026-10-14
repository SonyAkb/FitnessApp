---
id: CORE-02
title: "[Core] Шина событий внутри процесса"
assignee: SonyAkb
labels: [subject-1, module:core, type:feature, sprint-1]
milestone: "Sprint 1"
status: done
story_points: 2
related_us: [US-D1]
---
## Что сделать
Сделать простую шину событий, чтобы модули реагировали на действия друг друга без импорта чужих моделей.

## Детали / спецификация
- `backend-fit-baddy/app/events.py`: `EventBus.subscribe(name, handler)`, `publish(name, payload, db)`; обработчики вызываются синхронно в той же сессии БД.
- Имена событий: `user_registered`, `workout_completed`, `workout_missed`, `pet_leveled_up`.
- `register_event_handlers()` подключает `handlers.py` модулей при старте (lifespan).

## Критерии готовности
- [x] Модуль тренировок публикует событие, не импортируя модуль питомца
- [x] Повторный вызов `register_event_handlers()` не дублирует подписки

## Зависимости
- [CORE-01](CORE-01.md) — [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose

## Вопросы
Нет открытых вопросов.
