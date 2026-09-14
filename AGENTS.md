AGENTS.md — Team Development Rules

Educational Team Project

FitQuest is developed by a team of five students.

The repository is divided into five primary ownership areas:

01 Account & Schedule
02 Workouts
03 Pet & Gamification
04 Dashboard & Notifications
05 AI + Smart Watch Simulator + Subscription

When implementing a task, first determine which module owns the functionality.

⸻

Ownership

A developer should primarily modify their own module.

If a task requires changes to another module:

1. minimize the changes;
2. prefer using an existing public interface;
3. notify/document the cross-module dependency;
4. do not refactor the other module unnecessarily.

⸻

Parallel Work

Assume that other developers are actively changing the repository.

Therefore:

* avoid large unrelated refactors;
* avoid renaming shared structures without need;
* do not rewrite another developer’s code;
* keep commits focused;
* avoid changing shared APIs without checking consumers.

⸻

Mock Dependencies

During independent development, modules may use mocks.

For example:

Pet developer
    ↓
Mock WorkoutCompleted events

Dashboard developer:

Mock workout statistics

AI developer:

Mock workout history

This allows all five developers to work independently.

⸻

Integration First

When a module is ready, integrate it through the agreed contract.

Do not integrate by copying another module’s internal database logic.

⸻

Shared Contracts

Cross-module contracts should be documented.

Example:

WorkoutCompleted
{
    user_id: number,
    session_id: number,
    completed_at: datetime,
    duration_seconds: number
}

The exact contract should be changed only intentionally.

⸻

Do Not Overengineer

Remember that this is an educational MVP.

Do not introduce a new framework, infrastructure component or architectural pattern unless it solves a real project problem.

⸻

Mobile

The primary client is a responsive web application.

Always check that new UI works at approximately:

390px width   — iPhone
430px width   — large iPhone
360px width   — Android
768px width   — tablet
1440px width  — desktop

Do not create platform-specific code unless explicitly requested.

⸻

Demonstration Priority

When choosing between two implementations, prefer the one that makes the following demo easier:

Login
 ↓
Today's workout
 ↓
Complete workout
 ↓
XP gained
 ↓
Pet reacts
 ↓
Dashboard updates
 ↓
Notification

The final application must tell this story clearly.

AGENTS.md

Mission

You are a coding agent working on FitQuest.

Your job is to implement requested functionality while preserving the existing architecture and keeping the application easy to extend.

Do not rewrite the project unnecessarily.

⸻

1. Before Coding

Always:

1. Inspect the repository.
2. Read README.md.
3. Read CLAUDE.md if available.
4. Inspect the relevant module.
5. Search for existing implementations before creating new ones.
6. Identify tests related to the requested functionality.

Do not assume a component/service/model does not exist before searching.

⸻

2. Planning

For non-trivial tasks, create a short plan:

1. Backend changes
2. Database changes
3. API changes
4. Frontend changes
5. Tests
6. Documentation

Do not create unnecessary files.

⸻

3. Architecture

FitQuest is a modular monolith.

Preferred dependency:

Router
  ↓
Service / Use Case
  ↓
Repository
  ↓
Database

Do not put business logic into routers.

Do not put business logic into React components.

⸻

4. Module Boundaries

Modules:

auth
profile
workouts
pet
subscription
dashboard
notifications
ai
devices

A module owns its own:

* models
* schemas
* services
* repositories
* business rules

Avoid direct access to another module’s internals.

Use public services/contracts/events.

⸻

5. Domain Events

Use events when multiple modules need to react to one action.

Important events:

WorkoutCompleted
WorkoutMissed
GoalReached
StreakChanged
SubscriptionChanged
TelemetryReceived

Example:

WorkoutCompleted
      ├── Pet
      ├── Dashboard
      ├── Achievements
      └── Notifications

Do not duplicate workout completion logic in each consumer.

⸻

6. Database Rules

PostgreSQL is the primary database.

Every schema modification requires an Alembic migration.

Never:

* edit production schema manually;
* delete data to make tests pass;
* silently change existing data semantics;
* store passwords in plaintext.

Prefer explicit foreign keys and indexes for frequently queried fields.

⸻

7. API Rules

All API endpoints must use Pydantic request/response schemas.

Avoid returning raw ORM objects.

Use clear HTTP status codes.

Document endpoints through FastAPI/OpenAPI.

Prefer:

GET    /workouts/plans
POST   /workouts/plans
GET    /workouts/plans/{id}
PATCH  /workouts/plans/{id}
DELETE /workouts/plans/{id}

over inconsistent endpoint naming.

⸻

8. Error Handling

Do not expose internal exceptions to users.

Return stable application errors.

Never return:

* database credentials;
* stack traces;
* secrets;
* internal tokens.

⸻

9. Frontend

Use React + TypeScript.

Keep components small.

Prefer:

features/
components/
pages/
api/
hooks/
types/

Do not create a single giant component containing the entire application.

API access should be centralized.

Do not duplicate API URL construction across components.

⸻

10. State

Do not introduce a global state library unless there is a demonstrated need.

Prefer local state for local UI.

Server state should have a clear owner.

⸻

11. Security

Never commit:

.env
credentials
tokens
private keys
payment secrets
JWT secrets

Use environment variables.

Validate user-owned resources server-side.

Never trust IDs received from frontend.

Every protected endpoint must verify authorization.

⸻

12. AI

AI is an optional module.

The application must remain functional if the AI provider is unavailable.

Use an abstraction:

RecommendationService

Possible implementations:

MockRecommendationService
MLRecommendationService

AI failures should degrade gracefully.

⸻

13. Payments

Payment integrations must be behind an abstraction:

PaymentProvider

Webhook handlers must be idempotent.

Never trust frontend payment status.

The backend/payment provider is the source of truth.

⸻

14. Devices

Wearable integrations use providers.

Example:

DeviceProvider
├── SimulatorProvider
├── AppleHealthProvider
└── GarminProvider

Do not couple workout business logic directly to simulator implementation.

⸻

15. Tests

When adding functionality:

* add unit tests for business rules;
* add API tests for endpoints;
* add integration tests for important database flows.

Important test scenarios:

register
login
unauthorized access
create workout
complete workout
XP calculation
level up
streak
subscription access
webhook idempotency

⸻

16. Docker

The application must remain runnable with:

docker compose up --build

Do not introduce dependencies that require local installation unless absolutely necessary.

If adding a service:

1. Add Dockerfile.
2. Add docker-compose service.
3. Add environment variables.
4. Add health/dependency configuration where appropriate.
5. Update README.

⸻

17. Backward Compatibility

Before changing an existing API:

1. Search frontend consumers.
2. Search tests.
3. Search documentation.
4. Determine whether the API is already used.

Avoid breaking existing endpoints without a migration plan.

⸻

18. Refactoring

Do not perform unrelated refactoring while implementing a feature.

If you discover technical debt:

TODO:
<short description>

or document it separately.

Do not turn a small feature request into a complete rewrite.

⸻

19. Code Quality

Prefer:

* explicit code;
* type hints;
* small functions;
* descriptive names;
* clear errors;
* dependency injection;
* testable business logic.

Avoid:

* magic numbers;
* giant functions;
* hidden side effects;
* duplicated business logic;
* unnecessary abstractions.

⸻

20. Git

Keep changes logically grouped.

Prefer commits such as:

feat(auth): add JWT authentication
feat(workouts): add workout sessions
feat(pet): add XP progression
fix(workouts): prevent duplicate completion
test(pet): add level progression tests
docs: update workout API

Do not mix unrelated changes.

⸻

21. Final Verification

Before reporting completion:

[ ] Application builds
[ ] Relevant tests pass
[ ] Docker Compose starts
[ ] API works
[ ] Frontend works
[ ] Database migrations work
[ ] No secrets committed
[ ] Documentation updated

If something could not be tested, explicitly say what was not tested.

⸻

22. User Questions

Ask the user when ambiguity affects:

* architecture;
* database schema;
* external integrations;
* payments;
* authentication;
* deployment;
* data privacy;
* major UX behaviour.

Otherwise choose a sensible default and continue.

⸻

23. Golden Rule

Prefer the smallest clean implementation that solves the actual task.

Do not overengineer the MVP.

Make it work → make it clean → make it extensible.
