# Контракт API FitQuest

Общий контракт для `backend-fit-baddy` и `mobile-fit-baddy`. Префикс **`/api/v1`**. Аутентификация: **JWT Bearer** (`Authorization: Bearer <access_token>`), кроме явно открытых методов.

Симулятор и **будущий** Raspberry Pi используют **один и тот же Telemetry DTO**. Клиент не ветвится по источнику — только читает `source`.

Интерактивная спецификация после запуска: [http://localhost:8000/docs](http://localhost:8000/docs).

Базовый URL для эмулятора Android: `http://10.0.2.2:8000`.

---

## Общие соглашения

| Тема | Правило |
|---|---|
| Формат | JSON, UTF-8 |
| Время | ISO-8601 UTC (`2026-09-12T18:00:00Z`) |
| Ошибки | `{ "detail": "текст" }` или `{ "detail": [ { "loc", "msg", "type" } ] }` (валидация) |
| 401 | нет / просрочен токен |
| 403 | нет права (чужой ресурс или фича Pro) |
| 404 | ресурс не найден |
| 409 | конфликт (повторное complete, повторный email) |
| 422 | невалидное тело |
| Пароли | никогда не возвращаются |
| Секреты | не класть ключи в репозиторий и в этот документ |

Открытые эндпоинты: `POST /auth/register`, `POST /auth/login`, `POST /subscription/webhook` (mock-секрет в заголовке, не JWT пользователя). Health, если есть, тоже открыт.

---

## Telemetry DTO

Один объект для симулятора и будущего Pi:

```json
{
  "device_id": "sim-user-12",
  "user_id": 12,
  "steps": 8432,
  "heart_rate": 124,
  "calories": 420,
  "timestamp": "2026-09-12T18:01:00Z",
  "source": "simulator"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `device_id` | string | идентификатор устройства |
| `user_id` | int | владелец |
| `steps` | int | шаги ≥ 0 |
| `heart_rate` | int | пульс, уд/мин |
| `calories` | int | оценка ккал ≥ 0 |
| `timestamp` | datetime | момент снятия |
| `source` | string | `simulator` \| `raspberry_pi` |

`raspberry_pi` зарезервирован. В текущем MVP источник всегда `simulator`.

---

## События (in-process, не HTTP)

Публикуются backend после успешной записи. Android их не вызывает напрямую.

**WorkoutCompleted**

```json
{
  "user_id": 12,
  "session_id": 123,
  "completed_at": "2026-09-12T18:40:00Z",
  "duration_seconds": 2400
}
```

**WorkoutMissed**

```json
{
  "user_id": 12,
  "scheduled_id": 55,
  "missed_at": "2026-09-12T19:00:00Z"
}
```

Потребители: Pet, Dashboard, Notifications.

---

## Auth

### `POST /api/v1/auth/register`

Открытый. Создаёт пользователя и стартовое состояние питомца.

**Request**

```json
{
  "email": "user@example.com",
  "password": "string, min 8",
  "display_name": "Анна"
}
```

**Response `201`**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": 12,
    "email": "user@example.com",
    "display_name": "Анна",
    "goal": null
  }
}
```

`409` — email уже занят.

### `POST /api/v1/auth/login`

Открытый. JSON-тело (не form-urlencoded).

**Request**

```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response `200`** — те же `access_token`, `refresh_token`, `token_type`, `user`.  
`401` — неверные учётные данные.

### `GET /api/v1/auth/me`

JWT. **Response `200`**

```json
{
  "id": 12,
  "email": "user@example.com",
  "display_name": "Анна",
  "goal": "набрать силу",
  "weight_kg": 62.5,
  "fitness_level": "beginner"
}
```

---

## Profile

### `PATCH /api/v1/profile`

JWT. Частичное обновление.

**Request** (все поля опциональны)

```json
{
  "display_name": "Анна",
  "goal": "набрать силу",
  "weight_kg": 62.5,
  "fitness_level": "beginner"
}
```

`fitness_level`: `beginner` \| `intermediate` \| `advanced`.

**Response `200`** — тот же объект, что `GET /auth/me`.

---

## Schedule

Событие календаря привязано к пользователю и опционально к плану.

**ScheduleItem**

```json
{
  "id": 55,
  "title": "Силовая A",
  "starts_at": "2026-09-12T17:00:00Z",
  "ends_at": "2026-09-12T18:00:00Z",
  "plan_id": 3,
  "repeat_rule": null,
  "status": "planned"
}
```

`status`: `planned` \| `completed` \| `missed`.  
`repeat_rule`: `null` или RRULE-строка MVP (`FREQ=WEEKLY;BYDAY=MO,WE`).

### `GET /api/v1/schedule`

JWT. Query: `from`, `to` (ISO datetime, опционально).  
**Response `200`:** `ScheduleItem[]`.

### `POST /api/v1/schedule`

JWT. **Request:** `title`, `starts_at`, опционально `ends_at`, `plan_id`, `repeat_rule`.  
**Response `201`:** `ScheduleItem`.

### `PATCH /api/v1/schedule/{id}`

JWT. Частичное обновление тех же полей. **Response `200`:** `ScheduleItem`.

### `DELETE /api/v1/schedule/{id}`

JWT. **Response `204`.**

### `POST /api/v1/schedule/{id}/miss`

JWT. Помечает слот как пропущенный, публикует `WorkoutMissed`.

**Response `200`**

```json
{
  "id": 55,
  "status": "missed",
  "missed_at": "2026-09-12T19:00:00Z"
}
```

`409` — уже `completed` или `missed`.

---

## Workouts

**ExerciseInPlan**

```json
{
  "name": "Приседания",
  "sets": 3,
  "reps": 10,
  "weight_kg": 40,
  "rest_seconds": 90,
  "order_index": 0
}
```

**WorkoutPlan**

```json
{
  "id": 3,
  "name": "Силовая A",
  "description": "Ноги и спина",
  "exercises": []
}
```

### `GET /api/v1/workouts/plans`

JWT. **Response `200`:** `WorkoutPlan[]`.

### `POST /api/v1/workouts/plans`

JWT. **Request:** `name`, опционально `description`, `exercises[]`.  
**Response `201`:** `WorkoutPlan`.

### `POST /api/v1/workouts/sessions`

JWT. Старт сессии (таймер дальше локальный на телефоне).

**Request**

```json
{
  "plan_id": 3,
  "scheduled_id": 55
}
```

`scheduled_id` опционален.

**Response `201`**

```json
{
  "id": 123,
  "plan_id": 3,
  "scheduled_id": 55,
  "status": "in_progress",
  "started_at": "2026-09-12T18:00:00Z",
  "completed_at": null,
  "duration_seconds": null
}
```

### `POST /api/v1/workouts/sessions/{id}/complete`

JWT. Фиксирует факт выполнения, публикует `WorkoutCompleted`.

**Request** (тело опционально)

```json
{
  "duration_seconds": 2400
}
```

Если `duration_seconds` нет — backend считает от `started_at`.

**Response `200`**

```json
{
  "id": 123,
  "status": "completed",
  "started_at": "2026-09-12T18:00:00Z",
  "completed_at": "2026-09-12T18:40:00Z",
  "duration_seconds": 2400,
  "xp_awarded": 25
}
```

`409` — сессия уже завершена. Чек-лист упражнений **не обязан** уезжать на сервер в MVP.

### `GET /api/v1/workouts/history`

JWT. Query: `limit` (default 20), `offset`.

**Response `200`**

```json
{
  "items": [
    {
      "id": 123,
      "plan_name": "Силовая A",
      "status": "completed",
      "started_at": "2026-09-12T18:00:00Z",
      "completed_at": "2026-09-12T18:40:00Z",
      "duration_seconds": 2400
    }
  ],
  "total": 14
}
```

---

## Pet

### `GET /api/v1/pet`

JWT. Состояние персонажа — источник правды на сервере.

**Response `200`**

```json
{
  "id": 1,
  "name": "FitBuddy",
  "xp": 80,
  "xp_to_next_level": 100,
  "level": 2,
  "energy": 70,
  "mood": "happy",
  "streak_days": 3,
  "updated_at": "2026-09-12T18:40:05Z"
}
```

`mood`: `idle` \| `happy` \| `sad` \| `level_up` \| `neutral`. Android treats `neutral` as idle.

---

## Dashboard

### `GET /api/v1/dashboard/summary`

JWT. Агрегация, не копия сырых сессий.

Query: `period=week` (default).

**Response `200`**

```json
{
  "period": "week",
  "total_workouts": 14,
  "completed_workouts": 4,
  "missed_workouts": 1,
  "current_streak_days": 3,
  "xp": 80,
  "level": 2,
  "companion_mood": "happy",
  "steps_7d": 42100,
  "workouts_by_day": [
    { "date": "2026-09-07", "completed": 1 },
    { "date": "2026-09-08", "completed": 0 }
  ]
}
```

---

## Notifications

**Notification**

```json
{
  "id": 9,
  "title": "Тренировка засчитана",
  "body": "Питомец получил +25 XP",
  "is_read": false,
  "kind": "workout_completed",
  "created_at": "2026-09-12T18:40:06Z"
}
```

`kind` (информативно): `workout_completed` \| `workout_missed` \| `reminder` \| `motivation` \| `pet`.

### `GET /api/v1/notifications`

JWT. Query: `unread_only=true|false`.  
**Response `200`:** `Notification[]` (новые сверху).

### `POST /api/v1/notifications/{id}/read`

JWT. **Response `200`:** тот же объект с `is_read: true`.

---

## Devices и telemetry

### `POST /api/v1/devices/register`

JWT. Привязка устройства к пользователю.

**Request**

```json
{
  "device_id": "sim-user-12",
  "kind": "simulator"
}
```

`kind`: `simulator` \| `raspberry_pi` (второй — задел).

**Response `201`**

```json
{
  "device_id": "sim-user-12",
  "user_id": 12,
  "kind": "simulator",
  "status": "active"
}
```

### `GET /api/v1/telemetry/latest`

JWT. Последняя точка текущего пользователя.  
**Response `200`:** Telemetry DTO.  
`404` — ещё не было точек; клиент показывает «нет данных».

### `GET /api/v1/telemetry/history`

JWT. Query: `from`, `to`, `limit`.  
**Response `200`:** `TelemetryDTO[]`.

### `POST /api/v1/telemetry/simulate`

JWT. Генерация/публикация синтетической точки (тест). Тело опционально: если пусто — backend сам рисует правдоподобные значения.

**Request** (опционально)

```json
{
  "steps": 8432,
  "heart_rate": 124,
  "calories": 420
}
```

**Response `201`:** полный Telemetry DTO с `source: "simulator"`.

### `WS /api/v1/telemetry/ws`

JWT: токен в query `?token=` или в заголовке при handshake (как реализует мост).  
Сервер шлёт JSON Telemetry DTO по мере появления точек.

Клиент при обрыве: переподключение, иначе `GET /telemetry/latest` и статус «последнее известное».

---

## AI

Рекомендации **информационные**, не медицинский совет. Если провайдер недоступен — деградация с понятной ошибкой, приложение остаётся рабочим.

### `GET /api/v1/ai/recommend`

JWT. Может требовать план Pro (`403` с `detail`, что нужна подписка).

**Response `200`**

```json
{
  "id": 44,
  "recommendation": "Попробуйте увеличить вес в приседаниях на 2.5 кг",
  "reason": "стабильное выполнение плана на этой неделе",
  "disclaimer": "Это не медицинская рекомендация",
  "created_at": "2026-09-12T18:45:00Z"
}
```

На MVP допустим mock / лёгкое правило. Модель с Colab — замена за тем же контрактом.

### `GET /api/v1/ai/history`

JWT. **Response `200`:** массив тех же объектов.

---

## Subscription

MVP: **mock** Free / Pro. Реальный Stripe **не обязателен**.

### `GET /api/v1/subscription`

JWT.

**Response `200`**

```json
{
  "plan": "free",
  "status": "active",
  "current_period_end": null,
  "entitlements": ["workouts", "pet", "dashboard"]
}
```

Pro добавляет, например, `"ai_recommendations"`. Проверки вида `entitlements.can_use(...)`, не размазанный `if plan == "pro"` по всем модулям.

### `POST /api/v1/subscription/checkout`

JWT. Mock-оформление, без внешнего эквайера.

**Request**

```json
{
  "plan": "pro"
}
```

**Response `200`**

```json
{
  "checkout_id": "mock_chk_1",
  "status": "pending",
  "mock": true,
  "message": "Подтвердите оплату в приложении (демо)"
}
```

Клиент затем имитирует успех, вызывая webhook или отдельный confirm — для демо достаточно webhook ниже.

### `POST /api/v1/subscription/webhook`

Открытый для mock-провайдера. **Идемпотентный** по `event_id`.

Заголовок: `X-Mock-Signature: <значение из окружения, не из git>`.

**Request**

```json
{
  "event_id": "evt_1",
  "type": "checkout.completed",
  "user_id": 12,
  "plan": "pro"
}
```

**Response `200`**

```json
{
  "received": true,
  "duplicate": false,
  "plan": "pro",
  "status": "active"
}
```

Повтор с тем же `event_id`: `duplicate: true`, состояние не портится.

---

## Соответствие модулям

| Префикс | Модуль |
|---|---|
| `/auth`, `/profile`, `/schedule` | 1 Аккаунт и расписание |
| `/workouts` | 2 Тренировки |
| `/pet` | 3 Питомец |
| `/dashboard`, `/notifications` | 4 Дашборд и уведомления |
| `/devices`, `/telemetry`, `/ai`, `/subscription` | 5 ИИ, симулятор, подписка |
