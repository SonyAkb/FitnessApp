# FitQuest Android screens ↔ API

Base path `/api/v1`. Authenticated calls send `Authorization: Bearer <access_token>`.

## Splash

- `GET /auth/me` — if the stored token is valid, open home; otherwise login.

## Login / Register (`AuthActivity`)

- `POST /auth/register` `{email, password, display_name}` → `{access_token, token_type, user}`
- `POST /auth/login` `{email, password}` → `{access_token, token_type, user}`

## Den / Home (`HomeFragment`)

- `GET /pet` — name, xp, level, energy, mood (`idle|happy|sad|level_up`), streak_days. Mood picks the fox frame.
- `GET /schedule` — fallback teaser if dashboard has no `today_schedule`
- `GET /telemetry/latest` — pulse and steps if the dashboard fields are empty.

Actions:

- **Open quest board** → workout tab
- **Live watch** → telemetry screen

## Quest / Workout (`WorkoutFragment`)

- `GET /workouts/plans`
- `POST /workouts/plans` `{title, exercises:[{name, sets, reps, weight_kg?}]}`
- `POST /workouts/sessions` `{workout_plan_id}`
- `POST /workouts/sessions/{id}/complete` `{duration_seconds?}`
- `GET /workouts/history` → `{items: [Session], total}` (not a bare array)

- `POST /schedule` `{title, planned_at, workout_plan_id?, repeat_rule?}` — **Pin selected plan as today**

## Trail / Progress (`ProgressFragment`)

- `GET /dashboard/summary`
- `GET /ai/recommend` `{text, created_at}`

## Calls / Notifications (`NotificationsFragment`)

- `GET /notifications`
- `POST /notifications/{id}/read` (tap an unread row)

## Pack / Profile (`ProfileFragment`)

- `GET /auth/me`
- `PATCH /profile` `{display_name?, goal?, weight_kg?, fitness_level?}`
- `GET /subscription` `{plan, status}`
- `POST /subscription/checkout` (mock)

Also saves the API base URL locally (not an API call).

## Live watch (`TelemetryFragment`)

- `POST /devices/register` `{name}`
- `GET /telemetry/latest`
- `GET /telemetry/history`
- `POST /telemetry/simulate`
- WebSocket `WS /telemetry/ws` — client sends `{"token":"<jwt>"}` then reads live samples. REST polling is the fallback.

## 401

Any authenticated REST call that returns 401 clears the token and returns to login.
