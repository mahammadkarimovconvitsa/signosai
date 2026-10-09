# Signos — first-time setup

For Juri (or anyone else cloning this fresh). Two services: `backend/` (FastAPI +
Postgres, runs in Docker) and `frontend/` (Next.js, runs on your machine via pnpm).

## 0. Prerequisites

- Docker Desktop (running, not just installed)
- Node.js 20+ and `pnpm` (`npm i -g pnpm` if you don't have it)
- Nothing else — you do **not** need Python or Postgres installed locally; both
  only run inside Docker.

## 1. Clone

```bash
git clone https://github.com/mahammadkarimovconvitsa/signosai.git
cd signosai
```

## 2. Backend

```bash
cd backend
cp .env.example .env
```

Open `.env` and set at least:
- `JWT_SECRET_KEY` — any random string (e.g. `openssl rand -hex 32`)
- `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` — this becomes your first login,
  created automatically on first boot
- `GEMINI_API_KEY` — **optional.** Leave it blank if you don't have one yet.
  The AI/SI agents (network explanation, contracts summary, commercial SMS
  draft) fall back cleanly and the rest of the app works identically either
  way — you just won't see real agent-generated text in the approval queue
  until a key is set.

Everything else in `.env.example` has a sane default for local dev — leave it.

```bash
docker compose up --build        # starts Postgres + the API, ~1-2 min first time
```

Once it's up, **in a second terminal**:

```bash
docker compose exec api alembic upgrade head    # creates the schema
curl http://localhost:8000/api/v1/health/ready  # should return {"status":"ok"}
```

API docs: http://localhost:8000/docs

## 3. Load reference data

The app has **no mock data built in on purpose** — the DB starts empty, and
without reference data (sites, links, contracts, customers...) every screen
shows empty states and "Trigger fiber cut" has nothing to pick from.

If you have the hackathon dataset (`telecom_hackathon_data.zip`, ask the team
for it if you don't):

```bash
# from backend/, with the zip extracted somewhere, e.g. ~/Downloads/hackathon_data/
docker cp ~/Downloads/hackathon_data backend-api-1:/tmp/hackathon_data
docker compose exec api python scripts/import_hackathon_data.py /tmp/hackathon_data
```

This seeds 100 sites, 200 links, contracts, customers, etc. Two things it does
that are worth knowing (also documented at the top of the script):
- The dataset has no `cells.csv`, so one cell per site is synthesized
  deterministically — fine for demo purposes, not real revenue data.
- It replaces the dataset's placeholder password hashes with a real one for a
  disclosed dev password: **all imported `*@telecom.az` users log in with
  `Telecom123!`**.

No dataset handy? You can still click around with just your admin account —
most pages will say "no data loaded yet" until you add some (`docs/DATA_SCHEMA.md`
in `backend/` has the full schema + an example row per table if you want to
write your own seed data).

## 4. Frontend

```bash
cd ../frontend     # from repo root
pnpm install
cp .env.local.example .env.local
pnpm dev
```

Opens on **http://localhost:3001** — not 3000. That's deliberate (see
`frontend/README.md`); if 3000 is free on your machine and you'd rather use
it, change the `--port 3001` in `frontend/package.json`'s `dev` script and
update `CORS_ORIGINS` in `backend/.env` to match, then restart the backend
(`docker compose up -d --force-recreate api` — a plain `restart` does **not**
reload `.env`).

## 5. Log in

Go to http://localhost:3001, sign in with the `FIRST_ADMIN_EMAIL` /
`FIRST_ADMIN_PASSWORD` you set in step 2. You're an admin, so you'll see
everything including Settings/Users/Audit log.

## Resetting

`POST /api/v1/admin/reset` (as admin) clears incidents/alarms/actions and
puts every site/link back to "up" — reference data is never touched. Useful
between demo runs. The "Reset demo" button in the Incident Console does this
for you.

## If something's wrong

- `docker compose ps` — both `api` and `postgres` should say `healthy`
- `docker compose logs api --tail 50` — most backend issues show up here
- Backend tests: `docker compose exec api pytest` (99 tests, should all pass)
- Frontend: `pnpm exec tsc --noEmit && pnpm lint` (both should be clean)
