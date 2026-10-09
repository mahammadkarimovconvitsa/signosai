# Signos Backend

SI (Super Intelligence)-native operating system for mobile network operators — production FastAPI backend.

"SI" throughout this document refers to Super Intelligence (not "AI").

When a network failure happens (e.g. a fiber link is cut), the system collapses
hundreds of alarms into one incident, finds the root cause, identifies affected
enterprise customers and their SLA contracts, computes SLA deadlines, penalties,
revenue loss and total exposure, and has SI agents propose actions that humans
approve by role — every number traceable to its source rows, every action
recorded in an append-only audit log.

## Stack

Python 3.12 · FastAPI · PostgreSQL + SQLAlchemy 2.0 (async) · Alembic · JWT auth
(PyJWT + bcrypt) · Google Gemini (`google-genai`) · pytest · ruff · Docker

## Golden rule

**The database is the only source of data.** There is no mock data, seed script,
or JSON fixture anywhere in the application. Reference data (sites, cells,
links, customers, contracts, runbooks, market items, business config) is loaded
directly into Postgres by the data engineer — see
[`docs/DATA_SCHEMA.md`](docs/DATA_SCHEMA.md) for the exact shape, load order,
and business rules the data must satisfy. Business constants (default repair
ETA, compensation per subscriber, SLA at-risk threshold, portfolio thresholds)
live in the `business_config` table, with safe in-code fallback defaults only
so computations never crash on an empty table — the DB value always wins once
seeded.

## Setup

1. Copy the env file and fill in real secrets (at minimum `JWT_SECRET_KEY`,
   `FIRST_ADMIN_PASSWORD`, and `GEMINI_API_KEY` once you have one):
   ```bash
   cp .env.example .env
   ```
2. Build and start the stack:
   ```bash
   docker compose up --build
   ```
   This starts Postgres (with a `signos_test` database also created) and the
   API on `http://localhost:8000`. On first boot, the API creates an admin
   user from `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` if no admin exists
   yet, and starts a background worker that picks up any alarms written
   directly to the DB.
3. Run migrations (from a second terminal, once Postgres is healthy):
   ```bash
   docker compose exec api alembic upgrade head
   ```
4. Check it's alive:
   ```bash
   curl http://localhost:8000/api/v1/health/ready
   ```

API docs: `http://localhost:8000/docs`.

## What's implemented

- **Auth**: JWT access/refresh tokens, bcrypt hashing, role-based access
  (`admin` / `engineer` / `account_manager` / `viewer`), user management.
- **Network / Contracts / Market / Config**: read endpoints over sites, links,
  cells, contracts, market items, business config and the autonomy-level
  setting (all admin-write-gated where appropriate).
- **Domain services** (`app/services/`): correlation (collapses alarms into
  one incident, reuses an open incident for the same root-cause link, skips
  protected links by design), impact (sites → cells → customers → contracts),
  SLA (deadline/remaining-time/penalty math, `min(cap, ceil(hours_over) x
  rate)`), finance (revenue loss, total exposure), commercial (affected
  premium subscribers, compensation cost), portfolio (deterministic
  upgrade/keep/consolidate/decommission recommendation). Every number is
  returned as a `Metric` — `{value, unit, formula, inputs, sources[]}` — and
  `GET /api/v1/explain/{metric_id}` re-derives any of them on demand instead
  of trusting a cached figure.
- **Alarms**: an authenticated ingestion endpoint plus a background worker
  that polls for alarms written directly to the DB — either path triggers
  correlation and, if an incident results, the SI agents.
- **Incidents**: list/detail/current, timeline, ETA update, resolve (restores
  site/link status to up).
- **SI agents** (`app/services/agents/`): Network (incident explanation +
  runbook), Contracts (plain-language obligations), Commercial (bilingual
  compensation SMS draft) — Gemini structured output validated against a
  Pydantic schema, one retry/fallback policy shared by all three (3 attempts,
  backoff, then the incident's last stored output, then a clear "unavailable"
  state — never invented text), run as a background task so ingestion never
  blocks on the LLM. Each successful run proposes an action in the approval
  queue; the `auto_low_risk` autonomy level auto-executes low-risk ones.
- **Actions / approvals**: role-filtered list, approve/reject (role-checked,
  idempotent, conflicting re-transitions rejected).
- **Audit log**: append-only, filterable (admin only).
- **Real-time**: `GET /api/v1/incidents/{id}/stream` — Server-Sent Events,
  re-polls the DB and only emits when the incident actually changed.
- **Admin**: `POST /api/v1/admin/reset` clears incidents, actions, timeline,
  agent outputs and alarms, and restores site/link/cell status to up —
  reference data is never touched.
- **Production hardening**: global exception handlers (no stack traces in
  responses), structured JSON logs with a request id that propagates into
  background tasks, CORS from env, in-process rate limiting on auth/ingestion/
  admin endpoints, first-admin bootstrap, Docker healthchecks.

## Migrations

```bash
# generate a migration after changing models in app/models/
docker compose exec api alembic revision --autogenerate -m "describe the change"

# apply migrations
docker compose exec api alembic upgrade head

# roll back one revision
docker compose exec api alembic downgrade -1

# check models and the latest migration haven't drifted
docker compose exec api alembic check
```

> One sharp edge worth knowing: `sites.uplink_link_id` and `links` have a
> circular FK (a link references two sites; a site references its uplink
> link). `Base.metadata.create_all()` (used by the test suite) resolves this
> automatically via `use_alter=True`, but Alembic's autogenerated migration
> does **not** — it silently drops the constraint if left inline. The initial
> migration hand-splits it into `create_table` + a separate
> `op.create_foreign_key()` call after both tables exist. Keep that pattern
> for any future circular FK.

## Tests

Tests run against `TEST_DATABASE_URL` (a separate database from the one the
app uses), never against real/seeded data — enforced by a session-scoped
check that refuses to run if the two URLs match. Each test gets a dropped and
recreated schema. Gemini calls are mocked; the unit-math services (SLA,
finance, commercial, portfolio, correlation) have dedicated boundary-condition
tests since those numbers have to be correct to the unit.

```bash
docker compose exec api pytest
docker compose exec api pytest --cov
```

## Linting

```bash
docker compose exec api ruff check .
docker compose exec api ruff format .
```

## Reset (operational data only)

```bash
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Authorization: Bearer <admin access token>"
```

Clears incidents, actions, timeline events, agent outputs and alarms, and
restores every site/link/cell to `up`. Reference data loaded by the data
engineer (sites, cells, links, customers, contracts, runbooks, market items,
business config, users) is never touched.

## Project layout

```
app/
  core/            settings, security (JWT/hashing), exceptions, logging,
                    rate limiting, Gemini client, request-id middleware
  db/              async engine/session, declarative base
  models/          SQLAlchemy ORM models (one source of truth: the DB schema)
  schemas/         Pydantic request/response models
  repositories/    DB access, one per aggregate
  services/        business logic, orchestrates repositories
    agents/        Network/Contracts/Commercial Gemini agents + shared
                    retry/fallback policy
  workers/         background alarm-correlation poller
  api/v1/          routers — no business logic here
alembic/           migrations
tests/             pytest suite, isolated test database
docs/              DATA_SCHEMA.md + JSON Schemas for the data engineer
```
