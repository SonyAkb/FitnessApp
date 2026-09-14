# FitQuest backend (backend-fit-baddy)

Educational MVP API for the Android client and a software telemetry simulator.
This service is the server-bridge between the future Android app and test telemetry.
It does **not** talk to Raspberry Pi hardware.

Base URL: `http://localhost:8000`  
API prefix: `/api/v1`  
Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

## How to run

From the **repository root**:

```bash
cp .env.example .env   # first time only; edit SECRET_KEY
docker compose up --build
```

This starts PostgreSQL (`db`) and this backend (`backend` on port 8000).
The old React `frontend` service is still in Compose but is **not** required for this MVP.

Backend only:

```bash
docker compose up --build db backend
```

Health check: `GET http://localhost:8000/health`

## Schema

Tables are created on startup with SQLAlchemy `Base.metadata.create_all`
(no Alembic yet). If you previously ran the old `backend/` against the same
Compose Postgres volume, start with a fresh volume:

```bash
docker compose down
docker compose up --build db backend
```

The Compose file uses volume `fitbaddy_pgdata` so it does not reuse the old React-scaffold schema.

The Compose file uses volume `fitbaddy_pgdata` so it does not reuse the old React-scaffold schema.

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://fitquest:fitquest@db:5432/fitquest` | SQLAlchemy URL |
| `SECRET_KEY` | `CHANGE_ME_dev_only_secret` | JWT signing key (change in shared deploys) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifetime |
| `CORS_ORIGINS` | `*` | Comma-separated origins, or `*` |
| `POSTGRES_USER` / `PASSWORD` / `DB` | `fitquest` | Used by Compose for Postgres |

Never commit real secrets. Copy `.env.example` to `.env`.

## Auth

Protected routes expect:

```
Authorization: Bearer <access_token>
```

Register and login return `{access_token, token_type, user}`.

## Demo path (API)

1. `POST /api/v1/auth/register`
2. `POST /api/v1/workouts/plans`
3. `POST /api/v1/workouts/sessions`
4. `POST /api/v1/workouts/sessions/{id}/complete` → in-process `WorkoutCompleted`
5. `GET /api/v1/pet` — XP +25, mood `happy` (level-up at 100 XP)
6. `GET /api/v1/dashboard/summary`
7. `GET /api/v1/notifications`
8. `POST /api/v1/telemetry/simulate` then `GET /api/v1/telemetry/latest`

Live simulator (no Pi): `WS /api/v1/telemetry/ws` — after connect send `{"token":"<jwt>"}`, then samples every few seconds.

## Tests

```bash
cd backend-fit-baddy
pip install -r requirements.txt
pytest
```

Tests use in-memory SQLite and do not need Docker.

## Modules

| Folder | Owns |
|---|---|
| `app/modules/auth` | users, JWT, profile, schedule |
| `app/modules/workouts` | plans, sessions, history, `WorkoutCompleted` |
| `app/modules/pet` | XP, mood, level, streak (event consumer) |
| `app/modules/dashboard` | aggregated summary |
| `app/modules/notifications` | list/read + event-created notes |
| `app/modules/devices` | device register + telemetry simulator / WS |
| `app/modules/ai` | rule-based recommend + history |
| `app/modules/subscription` | free/pro sandbox checkout + idempotent webhook |

Cross-module reactions go through `app/events.py` (in-process). Workout code does not import pet models.

See `API.md` for request/response summaries.

Field names accept both the Android contract (`docs/API_CONTRACT.md`) and shorter aliases (`title`/`name`, `planned_at`/`starts_at`, `workout_plan_id`/`plan_id`). Responses include both where they differ.
