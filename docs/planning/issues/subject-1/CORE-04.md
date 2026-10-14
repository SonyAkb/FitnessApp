---
id: CORE-04
title: "[Core] Подключить Alembic и первую миграцию"
assignee: Hupubu
labels: [subject-1, module:core, type:tech, sprint-4]
milestone: "Sprint 4"
status: todo
story_points: 3
related_us: []
---
## Что сделать
Заменить `Base.metadata.create_all` при старте на миграции Alembic.

## Детали / спецификация
- `backend-fit-baddy/alembic.ini`, `alembic/env.py` (URL из `settings.DATABASE_URL`, `target_metadata = Base.metadata` с импортом моделей всех модулей).
- Первая миграция `0001_initial` = текущая схема из `docs/DATABASE.md` §1.
- В Docker: `alembic upgrade head` перед `uvicorn`.
- Тесты продолжают создавать схему через `create_all` (быстро).

## Критерии готовности
- [ ] `alembic upgrade head` на пустой БД создаёт все таблицы
- [ ] `alembic downgrade base` удаляет их
- [ ] README backend и `docs/DATABASE.md` обновлены
- [ ] CI зелёный

## Зависимости
Нет.

## Вопросы
Нужна ли миграция данных существующих dev-БД участников? По умолчанию — нет, том пересоздаётся.
