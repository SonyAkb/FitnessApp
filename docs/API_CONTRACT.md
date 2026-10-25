# Контракт API FitQuest

Общий контракт для `backend-fit-baddy` и `mobile-fit-baddy`. Префикс **`/api/v1`**. Аутентификация: **JWT Bearer** (`Authorization: Bearer <access_token>`), кроме явно открытых методов.

Симулятор и Raspberry Pi (`pi-fit-baddy`) используют **один и тот же Telemetry DTO**. Клиент не ветвится по источнику — только читает `source`.

> Это **целевой** контракт. Не реализованное пока отмечено как **(план)** (`/telemetry/ingest`, WS-рассылка сохранённых точек, настроение `sleeping`); построчный статус — `docs/planning/REQUIREMENTS_TRACE.md`, набор B.

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

Открытые эндпоинты: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /subscription/webhook` (mock-секрет в заголовке, не JWT пользователя), `GET /health`.

Аутентификация устройства: `POST /telemetry/ingest` принимает заголовок `X-Device-Token` (выдаётся в `POST /devices/register`), не JWT пользователя.

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

`source=simulator` — точки из `POST /telemetry/simulate`; `source=raspberry_pi` — точки, которые публикатор узла Pi присылает в `POST /telemetry/ingest` **(план)**. Для Pi `calories` рассчитывается по шагам (решение D-18).

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

### `POST /api/v1/auth/refresh`

Открытый. **Request:** `{ "refresh_token": "<jwt>" }`.  
**Response `200`:** новые `access_token`, `refresh_token`, `token_type`.  
`401` — токен просрочен, подделан или это access-токен (поле `typ` должно быть `refresh`). Защищённые методы принимают **только** токены с `typ=access`.

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
Границы: `sets` 1–10, `reps` 1–50, иначе `422`.

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

### `PATCH /api/v1/workouts/plans/{id}`

JWT. Частичное обновление плана. Все поля необязательные: `name` (или `title`), `description`, `exercises[]`.
Если `exercises` передан, он **заменяет весь список** упражнений.

**Response `200`:** `WorkoutPlan`.  
`404` — плана нет, он чужой или архивирован. `422` — выход за границы `sets`/`reps` или пустое название.

### `DELETE /api/v1/workouts/plans/{id}`

JWT. Архивирует план (заполняет `archived_at`), физически строка не удаляется. История тренировок по этому плану сохраняется.
Архивный план не попадает в `GET /workouts/plans`, по нему нельзя начать сессию.

**Response `204`** без тела. `404` — плана нет, он чужой или уже архивирован.

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

`mood`: `idle` \| `happy` \| `sad` \| `level_up` \| `neutral` \| `sleeping` (план). Android показывает `neutral` как `idle`.

Правила (решения D-13, D-14): +25 XP за тренировку и +5 XP за каждый день серии сверх первого; `xp_to_next_level` = `level × 100`; максимум 50 уровней. Настроение по дням без тренировки: 1–2 → `neutral`, 3–13 → `sad`, 14+ → `sleeping`.

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

`kind`: `simulator` \| `raspberry_pi`. Ответ содержит `device_token` — его вписывают в `.env` узла Pi (`DEVICE_TOKEN`). Повторная регистрация своего устройства → `200` с той же записью; чужой `device_id` → `409` (решение D-05).

**Response `201`**

```json
{
  "device_id": "sim-user-12",
  "device_token": "3f9c…",
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

### Подключение Raspberry Pi по коду сопряжения

Телефон и узел Pi не связываются напрямую: оба работают только с backend.

1. Приложение: `POST /api/v1/devices/pairing` (JWT, тело необязательно: `{"kind": "raspberry_pi", "name": "Pi в зале"}`) → `201 {"code": "525023", "kind": "raspberry_pi", "expires_at": "…"}`. Код одноразовый, живёт 10 минут; новый код отменяет предыдущий. Коды хранятся в памяти процесса backend.
2. Узел Pi: `POST /api/v1/devices/pair` (без JWT) `{"code": "525023", "device_id": "pi-livingroom-01"}` → `200` как у `devices/register` (`device_id`, `device_token`, `user_id`, `kind: "raspberry_pi"`). `404` — код неверный, использован или истёк; `409` — `device_id` уже привязан к другому пользователю; `422` — код не из 6 цифр. Повторное сопряжение того же устройства выдаёт новый токен, старый перестаёт работать.
3. Приложение видит устройство в `GET /api/v1/devices`.

### `GET /api/v1/devices`

JWT. Устройства пользователя без токенов: `[{"device_id", "name", "kind", "created_at", "last_seen_at"}]`, `last_seen_at` — время последней точки или `null`. `kind`: `simulator` | `raspberry_pi` | `health_connect`.

### `DELETE /api/v1/devices/{device_id}`

JWT. Отвязка: `204`; токен устройства больше не принимается (`ingest` → `401`), полученные точки остаются в истории. `404` — нет такого устройства у пользователя.

### `POST /api/v1/telemetry/ingest`

Открыт для устройств. Заголовок `X-Device-Token: <device_token>`. Пользователь определяется по токену, поле `user_id` в теле не передаётся.

**Request**

```json
{
  "device_id": "pi-livingroom-01",
  "steps": 4213,
  "heart_rate": 76,
  "calories": 168,
  "timestamp": "2026-10-14T12:00:00Z",
  "source": "raspberry_pi"
}
```

**Response `201`:** полный Telemetry DTO; `source` берётся из типа устройства.  
Повтор точки с тем же `device_id` и `timestamp` не сохраняется второй раз — `200` с уже сохранённой точкой (публикатор Pi доставляет «минимум один раз»).  
`401` — нет или неверный `X-Device-Token`; `403` — `device_id` не совпадает с токеном; `422` — отрицательные значения или `heart_rate` вне 30–230.

### `POST /api/v1/telemetry/batch`

JWT. Точки, которые приложение прочитало из Health Connect (туда пишут Mi Fitness, Zepp, Samsung Health, Fitbit и др.). Устройство `health-connect-<user_id>` (`kind: health_connect`) создаётся автоматически.

```json
{
  "source": "health_connect",
  "points": [
    {"steps": 3500, "heart_rate": 88, "calories": 0, "timestamp": "2026-10-25T09:15:00Z"}
  ]
}
```

От 1 до 500 точек; `steps` — накопленные с местной полуночи, `heart_rate` — средний за 5 минут, 30–230. **Response `200`:** `{"device_id", "accepted", "duplicates"}`; точки с уже полученным `timestamp` пропускаются.

### `WS /api/v1/telemetry/ws`

JWT: токен в query `?token=` или в заголовке при handshake (как реализует мост).  
Сразу после подключения сервер шлёт последнюю сохранённую точку, затем — каждую новую (из `simulate`, `ingest`, `batch`), проверяя раз в `TELEMETRY_WS_INTERVAL_SECONDS`. Если у пользователя нет реальных устройств (`raspberry_pi`, `health_connect`), сервер в том же цикле генерирует точку симулятора — демо работает без железа.

Клиент при обрыве: переподключение, иначе `GET /telemetry/latest` и статус «последнее известное».

---

## AI

Рекомендации **информационные**, не медицинский совет. Если провайдер недоступен — деградация с понятной ошибкой, приложение остаётся рабочим.

### `GET /api/v1/ai/recommend`

JWT. Требует entitlement `ai_recommendations` (тариф Pro): иначе `403` с `detail`, что нужна подписка.

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
  "plan": "pro",
  "status": "active",
  "mock": true,
  "message": "Sandbox checkout completed. Pro plan activated."
}
```

Checkout идёт через `PaymentProvider`. Sandbox-провайдер (MVP) подтверждает оплату сразу: ответ `status: "active"`, `plan: "pro"`, в `payments` — запись `succeeded`. Провайдер, который отвечает `pending`, не включает Pro — это делает только webhook ниже.

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

`type`: `payment.succeeded` (а также синонимы `checkout.completed`, `subscription.activated`) → Pro; `payment.failed` → тариф не меняется, платёж `failed`.  
`403` — заголовок `X-Mock-Signature` отсутствует или не равен `MOCK_WEBHOOK_SECRET` из окружения.

---

## Соответствие модулям

| Префикс | Модуль |
|---|---|
| `/auth`, `/profile`, `/schedule` | 1 Аккаунт и расписание |
| `/workouts` | 2 Тренировки |
| `/pet` | 3 Питомец |
| `/dashboard`, `/notifications` | 4 Дашборд и уведомления |
| `/devices`, `/telemetry`, `/ai`, `/subscription` | 5 ИИ, устройства, подписка |

Локальный API узла Raspberry Pi (`/device/status`, `/device/vitals/*`, `WS /device/stream`) описан в `docs/pi.md` §5 и в `pi-fit-baddy/README.md`. Он не является частью этого контракта: Android к нему не обращается.
