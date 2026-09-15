FitQuest — Educational Project Context

IMPORTANT: This is an educational team project

FitQuest is primarily a university/educational team project, not a production startup.

The project is being developed by 5 people.

The primary goal is:

1. demonstrate modular software architecture;
2. allow 5 developers to work in parallel;
3. demonstrate integration between independently developed modules;
4. provide a working MVP;
5. make the project easy to run on different operating systems;
6. demonstrate Docker, API, database, testing and documentation.

Do NOT optimize the architecture for millions of users.

Do NOT introduce infrastructure simply because it is common in production systems.

Architecture must be understandable to students and easy to demonstrate to an examiner.

⸻

Team Structure

There are 5 developers.

Each developer should have ownership of one primary business module.

The modules should be sufficiently independent to allow parallel development.

Module 1 — Account & Schedule

Owner responsibilities:

* registration;
* authentication;
* login/logout;
* roles;
* user profile;
* fitness goals;
* calendar;
* workout scheduling;
* recurring workouts.

Main entities:

User
Profile
Role
ScheduledWorkout

⸻

Module 2 — Workouts

Owner responsibilities:

* exercises;
* workout programs;
* workout plans;
* sets;
* repetitions;
* weight;
* workout execution;
* workout timer;
* workout history.

Main entities:

Exercise
WorkoutPlan
WorkoutPlanExercise
WorkoutSession
WorkoutSessionExercise
ExerciseSet

The module publishes:

WorkoutCompleted
WorkoutMissed

⸻

Module 3 — Pet & Gamification

Owner responsibilities:

* virtual pet;
* XP;
* levels;
* energy;
* mood;
* streaks;
* quests;
* achievements.

Main entities:

Pet
PetEvent
Quest
UserQuest
Achievement
UserAchievement

The module consumes:

WorkoutCompleted
WorkoutMissed
GoalReached

The pet should visibly react to user activity.

Example:

Workout completed
      ↓
+25 XP
      ↓
Pet becomes happier
      ↓
XP threshold reached
      ↓
Pet levels up

⸻

Module 4 — Dashboard, Statistics & Notifications

Owner responsibilities:

* main dashboard;
* weekly statistics;
* workout statistics;
* progress charts;
* activity calendar;
* streak visualization;
* notification center;
* workout reminders;
* motivational notifications.

Main entities:

Notification
ActivityStatistic

The module consumes events such as:

WorkoutCompleted
WorkoutMissed
GoalReached
SubscriptionChanged

Dashboard should aggregate data from the backend rather than duplicate the source of truth.

⸻

Module 5 — AI, Smart Watch Simulator & Subscription

This module consists of three relatively small subfeatures.

AI

Responsibilities:

* recommendation endpoint;
* recommendation history;
* simple ML model;
* model trained separately, for example in Google Colab;
* model inference.

For the initial MVP a mock recommendation is acceptable.

Example:

User workout history
       ↓
AI model
       ↓
"Try increasing squat weight by 2.5 kg"

AI recommendations are informational and should not be presented as medical advice.

Smart Watch Simulator

Responsibilities:

Generate synthetic:

steps
heart_rate
calories
timestamp

Example:

{
  "steps": 8432,
  "heart_rate": 124,
  "calories": 420
}

The simulator should communicate with the backend through an API.

It must NOT be tightly coupled to the workout module.

Subscription

Responsibilities:

* Free plan;
* Pro plan;
* feature restrictions;
* fake/sandbox payment flow;
* payment history;
* webhook demonstration.

For the educational MVP, a real payment provider is optional.

A mock payment provider is preferred unless the assignment specifically requires a real payment sandbox.

⸻

Module Ownership Rule

Each team member owns their module.

Other developers should not modify another module’s internal implementation unless necessary.

Cross-module integration should happen through:

* public service interfaces;
* API contracts;
* domain events;
* shared DTOs/contracts.

Avoid direct access to another module’s repositories.

Bad:

from pet.models import Pet

inside the workout business logic.

Better:

WorkoutCompleted
        ↓
Pet module

⸻

Parallel Development

The architecture MUST support five people working simultaneously.

Each developer should be able to:

1. develop their module;
2. write tests;
3. run their module locally;
4. use mock data for dependencies;
5. integrate with the main application later.

Do not require all five modules to be finished before any module can be demonstrated.

⸻

Integration Strategy

Use a shared API contract.

Example:

Workout module
POST /api/workouts/sessions/{id}/complete

returns:

{
  "session_id": 123,
  "status": "completed"
}

and produces:

WorkoutCompleted

Pet, Dashboard and Notifications can consume this event.

⸻

Educational Demonstration

The final application should allow an examiner to demonstrate this scenario:

1. User logs in
        ↓
2. Opens today's workout
        ↓
3. Starts workout
        ↓
4. Completes exercises
        ↓
5. Finishes workout
        ↓
6. System records workout
        ↓
7. Pet receives XP
        ↓
8. Pet changes mood / levels up
        ↓
9. Dashboard updates statistics
        ↓
10. Notification appears

This complete scenario is more important than implementing every planned feature.

⸻

Cross-Platform Requirement

The development team has:

* 1 Mac;
* 4 Windows PCs;
* 2 iOS devices;
* 3 Android devices.

The application must therefore be easy to run across different development environments.

Docker is the preferred solution for backend infrastructure.

The standard development command should be:

docker compose up --build

Developers should NOT need to manually install:

* PostgreSQL;
* Redis;
* Python;
* Node.js

for the standard Docker-based setup.

⸻

Mobile Requirement

Unless the assignment explicitly requires native mobile applications, the primary MVP should be a responsive web application.

The web UI must work on:

* desktop;
* iPhone;
* Android.

Use responsive layouts.

Do not create separate iOS and Android implementations unless explicitly required.

If mobile applications are later required, the existing REST API should be reusable by both platforms.

⸻

Complexity Rule

This is an educational project.

Prefer:

simple
understandable
testable
modular
demonstrable

over:

enterprise
distributed
over-engineered

Avoid introducing:

* Kubernetes;
* Kafka;
* RabbitMQ;
* microservices;
* complex event buses;
* service mesh;
* CQRS;
* event sourcing;

unless specifically required by the assignment.

A simple in-process event mechanism is sufficient for the MVP.

⸻

Five-Person Definition of Done

The final project should demonstrate:

Developer 1

Authentication + profile + schedule.

Developer 2

Workout planning + execution + history.

Developer 3

Pet + XP + gamification.

Developer 4

Dashboard + statistics + notifications.

Developer 5

AI + watch simulator + subscription.

All five modules must integrate into one application.

The final demonstration should show a complete user journey across multiple modules.

⸻

Primary Success Criterion

The project is successful if:

Five developers can independently implement their modules and then integrate them into one Dockerized application that can be demonstrated from desktop and mobile browsers.

Feature count is less important than clean module separation and successful integration.

FitQuest — Claude Project Instructions

1. Project

FitQuest — modular web application for fitness tracking with gamification.

Основная идея:

Пользователь тренируется в реальной жизни → система фиксирует прогресс → виртуальный питомец развивается вместе с пользователем.

Основные домены:

1. Authentication & Users
2. Profile
3. Calendar / Scheduling
4. Workouts
5. Gamification / Pet
6. Dashboard / Analytics
7. Notifications
8. Subscription
9. AI Recommendations
10. Smart Watch Simulator

⸻

2. Main Goal

Разрабатывать проект как MVP с возможностью дальнейшего масштабирования.

Главный архитектурный принцип:

Modular Monolith first, Microservices later if actually required.

Не создавать микросервисы без явной необходимости.

Каждый бизнес-модуль должен иметь чёткие границы и минимально зависеть от остальных модулей.

⸻

3. Tech Stack

Backend

* Python
* FastAPI
* SQLAlchemy 2.x
* Alembic
* PostgreSQL
* Redis
* Pydantic

Frontend

* React
* TypeScript
* Vite

Infrastructure

* Docker
* Docker Compose

API

REST API.

FastAPI должен автоматически предоставлять OpenAPI/Swagger.

Swagger:

/docs

⸻

4. Repository Structure

apps/
├── api/
│   └── app/
│       ├── core/
│       ├── db/
│       ├── api/
│       └── modules/
│           ├── auth/
│           ├── profile/
│           ├── workouts/
│           ├── pet/
│           ├── subscription/
│           ├── dashboard/
│           ├── notifications/
│           ├── ai/
│           └── devices/
│
└── web/
services/
└── simulator/
docs/
.ai/

Не смешивать frontend и backend business logic.

⸻

5. Modular Architecture

Каждый backend module должен стремиться к следующей структуре:

module/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── repository.py
├── service.py
├── events.py
└── tests/

Для маленького модуля допускается меньше файлов.

Не создавать файлы только ради архитектуры.

⸻

6. Dependency Rule

Предпочтительный flow:

HTTP Router
    ↓
Schema validation
    ↓
Application Service / Use Case
    ↓
Repository
    ↓
Database

Router не должен содержать бизнес-логику.

Плохой пример:

@router.post("/workouts")
def create_workout(...):
    db.add(...)
    if user.level > 5:
        ...

Хороший пример:

@router.post("/workouts")
def create_workout(...):
    return workout_service.create(...)

⸻

7. Cross-module Communication

Модули не должны напрямую зависеть от внутренних implementation details друг друга.

Например:

Pet не должен импортировать:

from workouts.models import WorkoutSession

для расчёта XP.

Вместо этого использовать application contracts или domain events.

Основные события:

WorkoutCompleted
WorkoutMissed
GoalReached
StreakChanged
SubscriptionChanged
TelemetryReceived

Пример:

WorkoutCompleted
       │
       ├── Pet → XP
       ├── Dashboard → statistics
       ├── Achievement → check achievements
       └── Notification → congratulations

⸻

8. Domain Ownership

Auth

Отвечает за:

* registration
* login
* JWT
* password hashing
* roles
* authentication

Не отвечает за fitness logic.

Profile

Отвечает за:

* user profile
* goals
* body metrics
* fitness level

Workouts

Отвечает за:

* exercises
* workout plans
* scheduled workouts
* workout sessions
* sets
* repetitions
* weights
* workout history

Pet

Отвечает за:

* XP
* level
* energy
* mood
* streak reaction
* pet state

Subscription

Отвечает за:

* plans
* subscriptions
* entitlements
* payments
* payment webhooks

Dashboard

Отвечает за:

* aggregations
* statistics
* progress
* charts data

Не хранит исходные workout records.

Notifications

Отвечает за:

* reminders
* motivational messages
* system notifications

AI

Отвечает за:

* recommendation requests
* model inference
* recommendation history

AI не должен напрямую изменять workout database.

Devices

Отвечает за:

* device integrations
* telemetry
* simulator
* future wearable providers

⸻

9. Database

Использовать PostgreSQL.

Все изменения схемы БД должны проходить через Alembic migrations.

Нельзя вручную менять production database schema.

Основные сущности:

users
profiles
exercises
workout_plans
workout_plan_exercises
scheduled_workouts
workout_sessions
workout_session_exercises
exercise_sets
pets
pet_events
quests
user_quests
achievements
user_achievements
subscriptions
subscription_events
payments
notifications
device_connections
telemetry
ai_recommendations

Историю тренировок не перезаписывать без необходимости.

Фактически выполненные тренировки должны сохраняться как historical data.

⸻

10. API

API должен быть:

* predictable
* RESTful
* versionable
* documented

На будущее предусмотреть:

/api/v1/...

Если проект ещё маленький и /api уже используется, не делать миграцию без необходимости.

Каждый endpoint должен иметь:

* request schema
* response schema
* error behaviour
* authentication requirement

⸻

11. Authentication

Использовать:

access token
refresh token

Пароли никогда не хранить в plain text.

JWT secret должен приходить из environment.

Никогда не commit:

.env
secrets
private keys
API tokens
payment credentials

⸻

12. Subscription

Не связывать бизнес-логику напрямую с конкретным payment provider.

Использовать abstraction:

PaymentProvider
    └── SandboxPaymentProvider

И:

SubscriptionService
    └── entitlement checks

Проверка доступа должна выглядеть концептуально:

entitlements.can_use(user, "ai_recommendations")

а не быть разбросана по проекту через:

if user.subscription == "pro":

⸻

13. AI

AI является отдельным модулем.

На первом этапе разрешён Mock AI:

MockRecommendationService

Позже:

MLRecommendationService

ML model должна быть заменяемой.

Не привязывать core domain к конкретной ML library.

Рекомендации AI не должны автоматически назначать опасные или медицинские нагрузки.

AI output должен рассматриваться как recommendation, а не medical advice.

⸻

14. Smart Watch Simulator

На MVP использовать simulator.

Simulator генерирует:

steps
heart_rate
calories
timestamp

Simulator должен быть отдельным service:

services/simulator

Позже можно добавить:

Apple Health
Google Fit
Garmin
Fitbit

через provider abstraction.

⸻

15. Gamification

Базовая модель:

XP
Level
Energy
Mood
Streak
Achievements
Quests

Пример:

WorkoutCompleted
        ↓
calculate XP
        ↓
update pet
        ↓
check level
        ↓
check achievements

Игровую логику не размещать во frontend.

Frontend только отображает состояние.

⸻

16. Docker

Проект должен запускаться одинаково на:

* Linux
* macOS
* Windows

Основная команда:

docker compose up --build

Основные services:

db
redis
api
web
simulator

Не требовать от разработчика локальной установки PostgreSQL/Redis/Python/Node для стандартного запуска проекта.

⸻

17. Environment

Все environment-specific настройки должны находиться в environment variables.

Использовать:

.env.example

Но не commit настоящий .env.

⸻

18. Testing

Минимально:

Unit tests
Integration tests
API tests

Особенно тестировать:

* authentication
* workout completion
* XP calculation
* level progression
* streak
* subscription entitlements
* payment webhook idempotency

Перед завершением задачи запускать релевантные tests.

⸻

19. Frontend Rules

Frontend должен быть feature-oriented.

Предпочтительная структура:

src/
├── app/
├── pages/
├── features/
│   ├── auth/
│   ├── workouts/
│   ├── pet/
│   ├── dashboard/
│   └── profile/
├── components/
├── api/
├── hooks/
└── types/

Не помещать domain logic backend в React.

API calls централизовать.

Не создавать огромный App.tsx.

⸻

20. UI/UX

FitQuest должен ощущаться как fitness game, а не как корпоративная CRM.

Основные UX priorities:

1. User immediately understands today’s workout.
2. Progress is visible.
3. Pet creates emotional feedback.
4. Completing workout feels rewarding.
5. Dashboard is understandable within seconds.

Но не переусложнять MVP анимациями.

⸻

21. Development Workflow

Перед реализацией крупной задачи:

1. Изучить существующую архитектуру.
2. Найти связанные modules.
3. Определить owner каждого изменения.
4. Проверить existing conventions.
5. Составить небольшой implementation plan.
6. Только потом менять код.

После изменения:

1. Run formatter/linter.
2. Run relevant tests.
3. Check Docker build.
4. Check API contract.
5. Проверить, не нарушены module boundaries.

⸻

22. Changing Architecture

Если новая задача требует изменения архитектуры:

Не делать silently.

Сначала определить:

Problem
Current architecture
Proposed solution
Trade-offs

Если решение существенно меняет архитектуру, добавить запись в:

.ai/decisions.md

⸻

23. Definition of Done

Задача считается завершённой, когда:

* код реализован;
* module boundaries соблюдены;
* migrations созданы, если нужна БД;
* tests добавлены/обновлены;
* API documented;
* Docker продолжает запускаться;
* .env.example обновлён при необходимости;
* нет secrets;
* нет TODO в критическом execution path;
* README/docs обновлены при необходимости.

⸻

24. Important Rule

Не пытайся реализовать весь FitQuest сразу.

Работай вертикальными slices.

Например:

Registration
    ↓
Login
    ↓
Profile
    ↓
Create workout
    ↓
Complete workout
    ↓
XP
    ↓
Pet
    ↓
Dashboard

Каждый slice должен быть реально запускаемым.

⸻

25. Communication

Если требования неоднозначны и решение влияет на архитектуру, задай вопрос пользователю.

Особенно обязательно уточнять:

* payment provider;
* authentication providers;
* pet visual design;
* AI model format;
* deployment target;
* data retention requirements;
* notification provider;
* wearable integration.

Если вопрос не блокирует реализацию, выбери разумный default и явно укажи его.

⸻

26. Don’t Overengineer

Не добавлять без необходимости:

* Kubernetes
* Kafka
* RabbitMQ
* microservices
* service mesh
* CQRS
* event sourcing
* distributed tracing
* сложный DDD framework

MVP должен оставаться простым.

Главная цель:

Working product with clean module boundaries.
