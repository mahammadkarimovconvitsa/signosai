# Signos Frontend

The console for [Signos](../backend/README.md) — Next.js (App Router) + TypeScript +
Tailwind, talking to the FastAPI backend over plain `fetch`.

## Stack

Next.js 16 · React 19 · TypeScript · Tailwind v4 · TanStack Query · react-leaflet

No state-management library beyond React Query (server cache) and a couple of small
Context providers (auth, the "why this number" explain drawer) — the app doesn't need
more than that.

## Setup

```bash
pnpm install
cp .env.local.example .env.local   # if present; otherwise see below
pnpm dev
```

Runs on **port 3001**, not 3000 — this machine already has an unrelated project bound
to 3000. The backend's `CORS_ORIGINS` includes `http://localhost:3001` to match; if you
change the frontend port, update that too.

`.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

The backend must be running (see `../backend/README.md`) with at least some reference
data loaded (sites, links, cells, customers, contracts — the data engineer's job per
`../backend/docs/DATA_SCHEMA.md`) for the console to show anything beyond empty states.

## Structure

```
src/
  app/
    login/              public route
    (app)/              everything behind auth, wrapped by a shared shell
      page.tsx            Incident Console — the centerpiece
      network/            sites, links, cells
      contracts/          contract reference list
      commercial/         full commercial summary for the active incident
      portfolio/          site recommendations
      market/             market items
      audit/              admin only
      settings/           admin only — business config
      users/              admin only — user management
  components/           shared UI: badges, Card, MetricValue, Sidebar, Topbar,
                         the autonomy dial, the explain drawer, the Leaflet map
  lib/
    types.ts             TypeScript types mirroring backend/app/schemas/*.py exactly
    api.ts                typed functions for every backend endpoint
    http.ts               fetch wrapper: token storage, auto-refresh-on-401
    auth-context.tsx       current user, login/logout
    metric-ids.ts          builds the explain-endpoint id strings (see below)
```

## Auth

JWT access + refresh tokens in `localStorage`. `http.ts` attaches the access token to
every request and, on a 401, transparently refreshes once and retries; if the refresh
token is also dead it clears storage and the auth context redirects to `/login`.

## Role-based UI

The sidebar and topbar hide admin-only items (`Audit log`, `Settings`, `Users`, the
autonomy dial) for non-admin users, and the approval queue only renders Approve/Reject
for actions owned by the current user's role (or any action, for admins) — but this is
just UX convenience. **The backend is the actual authorization boundary**: every
list/mutation endpoint re-checks the role server-side regardless of what the frontend
shows, so hiding a button here is never the only thing standing between a role and an
action it shouldn't take.

## "Why this number" (the explain drawer)

The backend never persists a `Metric` as its own row — every number is recomputed from
the DB on each request, formula and source rows included. So `GET /explain/{metric_id}`
takes a composite id like `finance.total_exposure:<incident_id>` or
`sla.deadline:<incident_id>:<contract_id>` and re-dispatches to the same service method
that produced the number on screen, rather than looking anything up by a stored id.
`lib/metric-ids.ts` is the single place that builds these strings — if you add a new
explainable metric, add it there, matching whatever
`backend/app/services/explain_service.py` expects exactly (domain, field name, and
param order all have to line up).

## The "Trigger fiber cut" demo control

Posts 10 synthetic `link_down` alarms against a site you pick from the ones that have
an `uplink_link_id` set — it doesn't fabricate its own site, it only works against real
reference data already loaded in the DB. This is what drives the whole "one fiber cut
becomes one incident" demo path end to end: correlation creates the incident, the
Gemini agents run as a background task on the backend (or fall back cleanly if no
`GEMINI_API_KEY` is set), and the console starts polling everything incident-scoped
every 5 seconds.

## Known dev-only noise

Next.js 16's dev server logs an "instant navigation" diagnostic for the `(app)` client
component routes on every request. It's purely a dev-mode prefetch-validation warning —
confirmed it doesn't affect rendering or behavior — and doesn't appear in a production
build. Not worth suppressing with `export const instant = false` given the uncertainty
around that export's interaction with `"use client"` route segments on a version this
new; revisit if it ever shows up as more than console noise.

## Verification

This was built and verified against the real running backend in a browser throughout
(not just "it compiles") — the full alarm-to-incident flow, role-based access for both
admin and engineer accounts, the explain drawer, and every page's empty/loaded states
were all exercised live. `pnpm exec tsc --noEmit` and `pnpm lint` are both clean.
