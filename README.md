# FitQuest — фитнес-трекер с игровым персонажем

Пользователь тренируется в жизни → система фиксирует прогресс → виртуальный питомец растёт вместе с ним.

**Текущий MVP:** нативный Android-клиент (Java) и FastAPI-мост с PostgreSQL. Телеметрия в тесте идёт от симулятора. Raspberry Pi — **план**, в этом срезе не реализован. Оплата Pro — **mock checkout**, Stripe не обязателен.

> Учебный командный проект (5 человек). Цель — модульная архитектура, параллельная разработка и сквозная демонстрация, а не продакшен на миллионы пользователей.

---

## Документация

| Документ | Содержание |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Три папки, телеметрия за одним контрактом, 5 модулей, in-process события |
| [docs/USER_STORIES.md](docs/USER_STORIES.md) | Пользовательские истории, порядок вызовов mobile/backend, диаграммы |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Общий REST/WS контракт `/api/v1` |
| [docs/RUN.md](docs/RUN.md) | Как поднять Docker + Android Studio |
| [docs/PLAN.md](docs/PLAN.md) | Ранний план React-каркаса (части про веб-клиент и обязательный Stripe **устарели** для текущего MVP) |

---

## Целевые папки

```
backend-fit-baddy/    FastAPI + PostgreSQL — мост /api/v1
mobile-fit-baddy/     Android Java — основной клиент
pi-fit-baddy/         Raspberry Pi — будущее (датчики → тот же Telemetry DTO)
```

Исторические `backend/` и `frontend/` (React) — черновик каркаса. **Основной клиент — Android**, React-заглушка для демо не нужна.

---

## Как запустить MVP

Подробности: [docs/RUN.md](docs/RUN.md).

1. `docker compose up --build` — PostgreSQL и FastAPI (`:8000`).
2. Android Studio → проект `mobile-fit-baddy/`.
3. Base URL эмулятора: `http://10.0.2.2:8000`.
4. Swagger: [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Тестовая и будущая боевая телеметрия

Клиент работает с одним DTO (`steps`, `heart_rate`, `calories`, `source`, …):

- **Тест (сейчас):** симулятор, `POST /api/v1/telemetry/simulate`, `source=simulator`.
- **Боевой режим (позже):** Raspberry Pi в `pi-fit-baddy/`, `source=raspberry_pi`.

```
Android  ──REST/WS──►  FastAPI  ──►  источник
                                   тест: эмулятор
                                   бой:  Pi (план)
```

---

## Модули команды

1. Аккаунт и расписание — регистрация, JWT, профиль, цели, календарь.
2. Тренировки — планы, сессия, чек-лист, локальный таймер, история.
3. Питомец — XP, уровень, настроение, стрик (реакция на `WorkoutCompleted` / `WorkoutMissed`).
4. Дашборд и уведомления — неделя, история, центр уведомлений.
5. ИИ + симулятор часов + подписка — mock-рекомендации, телеметрия, Free/Pro (mock).

Сквозной поток: вход → сегодняшняя тренировка → complete → XP → питомец → дашборд → уведомление → живая телеметрия. См. [docs/USER_STORIES.md](docs/USER_STORIES.md).

---

## Стек

| Слой | Технология |
|---|---|
| Клиент | Android, Java |
| Мост | Python, FastAPI, `/api/v1` |
| БД | PostgreSQL |
| Инфра | Docker Compose |
| Телеметрия MVP | симулятор (тот же DTO, что планируется у Pi) |
| Оплата MVP | mock checkout + идемпотентный mock-webhook |

Секреты и ключи не коммитить (`.env` вне git).
