# Схема базы данных FitQuest

PostgreSQL 16 (в тестах — SQLite in-memory). Модели — SQLAlchemy 2.x в `backend-fit-baddy/app/modules/*/models.py`.
Схема управляется миграциями Alembic (`backend-fit-baddy/alembic/`, задача [CORE-04](planning/issues/subject-1/CORE-04.md)); см. раздел 4.

Каждая таблица принадлежит **одному** модулю. Чужой модуль не пишет в неё и не импортирует её модель (правило — `docs/ARCHITECTURE.md`, раздел «Границы модулей»).

## 1. Текущая схема (по коду на 27.10.2026)

```mermaid
erDiagram
  users ||--|| profiles : "has"
  users ||--o{ scheduled_workouts : "plans"
  users ||--o{ workout_plans : "owns"
  workout_plans ||--o{ workout_plan_exercises : "contains"
  users ||--o{ workout_sessions : "performs"
  workout_plans ||--o{ workout_sessions : "template of"
  scheduled_workouts |o--o{ workout_sessions : "started from"
  scheduled_workouts }o--o| workout_plans : "uses"
  users ||--|| pets : "has"
  users ||--o{ notifications : "receives"
  users ||--o{ devices : "registers"
  users ||--o{ telemetry_points : "produces"
  users ||--o{ ai_recommendations : "gets"
  users ||--|| subscriptions : "has"
  users ||--o{ payments : "pays"

  users {
    int id PK
    string email UK
    string hashed_password
    string display_name
    string role "user | admin"
    bool is_active
    datetime created_at
  }
  profiles {
    int id PK
    int user_id FK,UK
    string goal "nullable"
    float weight_kg "nullable"
    string fitness_level "nullable"
  }
  scheduled_workouts {
    int id PK
    int user_id FK
    string title
    datetime planned_at
    int workout_plan_id FK "nullable"
    string repeat_rule "nullable, не разворачивается"
    string status "planned | missed | completed"
    datetime ends_at
    datetime missed_at
    datetime created_at
  }
  workout_plans {
    int id PK
    int user_id FK
    string title
    string description
    datetime created_at
    datetime archived_at "nullable, NULL = план активен (мягкое удаление)"
  }
  workout_plan_exercises {
    int id PK
    int plan_id FK
    string name "свободный текст"
    int sets
    int reps
    float weight_kg
    int rest_seconds
    int order_index
  }
  workout_sessions {
    int id PK
    int user_id FK
    int workout_plan_id FK
    int scheduled_id FK "nullable"
    string status "in_progress | completed"
    datetime started_at
    datetime completed_at
    int duration_seconds
    int xp_awarded
  }
  pets {
    int id PK
    int user_id FK,UK
    string name
    int xp
    int level
    int energy "0..100"
    string mood "idle | happy | sad | level_up | neutral"
    int streak_days
    date last_activity_date
    datetime updated_at
  }
  users ||--o{ user_quests : "does"
  users ||--o{ user_achievements : "earns"
  quests ||--o{ user_quests : "assigned"
  achievements ||--o{ user_achievements : "earned"
    quests {
    int id PK
    string code UK "preset: one_workout_today | three_workouts_week"
    string title
    string period "daily | weekly"
    int target
    int xp_reward
  }
  user_quests {
    int id PK
    int user_id FK
    int quest_id FK
    int progress
    datetime period_start
    datetime completed_at "nullable"
  }
  achievements {
    int id PK
    string code UK "preset: first_workout | three_in_row | week_no_miss"
    string title
    int xp_reward
  }
  user_achievements {
    int id PK
    int user_id FK
    int achievement_id FK
    datetime earned_at
  }
  
  notifications {
    int id PK
    int user_id FK
    string title
    text body
    string kind "workout_completed | workout_missed | pet"
    bool is_read
    datetime created_at
  }
  devices {
    int id PK
    string device_id UK
    string device_token
    int user_id FK
    string name
    string kind "simulator | raspberry_pi"
    datetime created_at
  }
  telemetry_points {
    int id PK
    string device_id
    int user_id FK
    int steps
    int heart_rate
    int calories
    datetime timestamp
    string source "simulator | raspberry_pi"
  }
  ai_recommendations {
    int id PK
    int user_id FK
    text text
    datetime created_at
  }
  subscriptions {
    int id PK
    int user_id FK,UK
    string plan "free | pro"
    string status
    datetime updated_at
  }
  payments {
    int id PK
    int user_id FK
    int amount "в центах"
    string currency
    string status
    string provider "sandbox"
    datetime created_at
  }
  webhook_events {
    int id PK
    string event_id UK "идемпотентность"
    string event_type
    int user_id "без FK"
    datetime processed_at
  }
```

| Таблица | Модуль (папка) | Владелец |
|---|---|---|
| `users`, `profiles`, `scheduled_workouts` | `auth` | @NastyaZhilinaRis2 |
| `workout_plans`, `workout_plan_exercises`, `workout_sessions` | `workouts` | @Hupubu |
| `pets`, `quests`, `user_quests`, `achievements`, `user_achievements` | `pet` | @SonyAkb |
| `notifications` | `notifications` | @Ananasic07 |
| `devices`, `telemetry_points` | `devices` | @MouseViolin |
| `ai_recommendations` | `ai` | @MouseViolin |
| `subscriptions`, `payments`, `webhook_events` | `subscription` | @MouseViolin |

## 2. Планируемые таблицы (нужны для закрытия требований)

Не реализованы. Каждая — отдельная задача в `docs/planning/issues/`.

```mermaid
erDiagram
  exercises ||--o{ workout_plan_exercises : "picked from"
  workout_sessions ||--o{ workout_session_exercises : "includes"
  workout_session_exercises ||--o{ exercise_sets : "logged as"
  users ||--o{ pet_events : "history of pet"
  quests ||--o{ user_quests : "assigned"
  achievements ||--o{ user_achievements : "earned"

  exercises {
    int id PK
    string name UK
    string muscle_group "legs | chest | back | ..."
    string description
  }
  workout_session_exercises {
    int id PK
    int session_id FK
    int exercise_id FK "nullable"
    string name
    int order_index
    string status "pending | done | skipped"
  }
  exercise_sets {
    int id PK
    int session_exercise_id FK
    int set_index
    int target_reps
    float target_weight_kg
    int actual_reps
    float actual_weight_kg
    string status "done | skipped"
    datetime completed_at
  }
  pet_events {
    int id PK
    int user_id FK
    string kind "xp | level_up | mood | return_bonus"
    int xp_delta
    string payload
    datetime created_at
  }
  quests {
    int id PK
    string code UK
    string title
    string period "daily | weekly"
    int target
    int xp_reward
  }
  user_quests {
    int id PK
    int user_id FK
    int quest_id FK
    int progress
    datetime period_start
    datetime completed_at
  }
  achievements {
    int id PK
    string code UK "first_workout | three_in_row | week_no_miss"
    string title
    int xp_reward
  }
  user_achievements {
    int id PK
    int user_id FK
    int achievement_id FK
    datetime earned_at
  }
```

Также планируется:
- `profiles.goal` / `profiles.fitness_level` — ограничить значениями (`weight_loss | muscle_gain | endurance | health`; `beginner | intermediate | advanced`, по умолчанию `beginner`).
- `pets.mood` — добавить `sleeping` (решение D-14).
- `notification_settings` (user_id, reminders_enabled, reminder_offsets, motivational_enabled) — для US-F1/F2.
- `payments.status` — `pending | succeeded | failed`, `subscriptions.current_period_end`.

## 3. Правила

- Изменения схемы — только через миграции Alembic (`alembic revision --autogenerate -m "..."`), результат проверять вручную.
- Историю тренировок (`workout_sessions`, `exercise_sets`) не перезаписывать: это исторические данные.
- `webhook_events.event_id` уникален — основа идемпотентности webhook.
- Даты хранятся с часовым поясом (`timestamptz`), в API — ISO-8601 UTC.

## 4. Миграции

Миграции лежат в `backend-fit-baddy/alembic/versions/`. Миграция `0001_initial` создаёт схему из §1 (14 таблиц, включая `workout_plans.archived_at`), `downgrade` удаляет её. Служебная таблица `alembic_version` хранит номер применённой миграции и в схему приложения не входит.

- Адрес БД берётся из `settings.DATABASE_URL`.
- В Docker миграции применяются при старте backend (`alembic upgrade head` перед `uvicorn`).
- Изменили модель — создайте новую миграцию и обновите §1 этого документа.
- Новый файл `models.py` нужно импортировать в `alembic/env.py`.
- Тесты миграции не используют: схема создаётся через `Base.metadata.create_all` (SQLite in-memory).