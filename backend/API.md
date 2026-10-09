# SignalOS API — Stage 1

Base URL: `http://localhost:8000` (or whichever port you run `uvicorn app.main:app` on).

Stage 1 covers schema, seed data and the demo incident endpoint. Business logic
(SLA/finance/correlation), AI agents, and governance (approvals/audit/autonomy)
land in later stages and will extend this doc.

## `GET /api/sites`

Used by: **Baku map**.

Returns all 40 sites. `status` is `"down"` for the 9 sites currently cut off by
the FL-07 scenario, `"up"` otherwise.

```json
[
  {
    "id": "S01",
    "name": "Binagadi Site 1",
    "lat": 40.45697,
    "lng": 49.7887,
    "district": "Binagadi",
    "uplink_link_id": "FL-07",
    "energy_cost_azn_month": 620.02,
    "status": "down"
  }
]
```

## `GET /api/incident/demo`

Used by: **incident console** (map overlay, timeline, SLA/revenue panels, approval queue).

Returns the single seeded demo incident (`INC-001`), fully nested. See
[`data/mock_incident.json`](../data/mock_incident.json) for a complete real example
(auto-exported from the seed, always in sync with what this endpoint returns).

```json
{
  "id": "INC-001",
  "root_cause": "Fiber link FL-07 cut between Nasimi (S10) and Binagadi (S01)",
  "started_at": "2026-10-09T09:04:30.108469",
  "status": "open",
  "alarm_count": 150,
  "affected_sites": [ /* SiteOut[], 9 items */ ],
  "timeline": [
    { "ts": "...", "label": "alarms_received", "detail": "150 alarms received from 9 sites" },
    { "ts": "...", "label": "correlated", "detail": "Root cause: FL-07 link down" },
    { "ts": "...", "label": "sla_flagged", "detail": "Bank HQ SLA at risk: 2h40min remaining" },
    { "ts": "...", "label": "exposure_computed", "detail": "Revenue loss ~AZN 38/min, exposure tracked" },
    { "ts": "...", "label": "actions_proposed", "detail": "3 actions proposed for approval" }
  ],
  "actions": [
    { "id": "ACT-01", "agent": "network", "proposal": "...", "owner_role": "engineer", "status": "proposed", "sources": ["alarm:AL-0001..AL-0150", "link:FL-07"] },
    { "id": "ACT-02", "agent": "commercial", "proposal": "...", "owner_role": "account_manager", "status": "proposed", "sources": ["segment:premium", "contract:CT-01"] },
    { "id": "ACT-03", "agent": "contracts", "proposal": "...", "owner_role": "account_manager", "status": "proposed", "sources": ["contract:CT-01", "customer:CUST-01"] }
  ]
}
```

Note: `started_at` is wall-clock server time at seed time, 20 minutes before
"now" — i.e. the SLA clock (180 min restore window on contract `CT-01`) always
has ~160 minutes (2h40min) remaining right after a fresh seed/reset. SLA/finance
math itself (deadline, remaining time, penalty, revenue lost, exposure) is
**Stage 2** — not yet exposed via the API.

## `GET /api/incidents/{incident_id}`

Same shape as above, for a specific incident id. Returns `404` if not found.
Currently only `INC-001` exists.

## `POST /api/incidents/trigger`

Used by: **"Trigger fiber cut" button**.

Stage 1 stub: re-seeds the full dataset from scratch and returns the fresh
`INC-001` (same effect as `/api/reset`). Stage 2 will make this generate a
*live* alarm storm and run real correlation instead of reusing the seed.

## `POST /api/reset`

Used by: **"Reset demo" button**.

Drops and recreates all tables, then reseeds the full dataset (40 sites, 120
cells, 12 enterprise customers, ~25 contracts, the FL-07 incident with its 150
alarms, timeline, actions and audit log). Idempotent — always returns to the
same starting state. Returns the fresh `INC-001`.

## Known scenario numbers (for sanity-checking the UI)

- Cut link: `FL-07`, unprotected spur from Nasimi hub to Binagadi hub, feeding
  all 9 Binagadi sites (27 cells).
- Revenue lost: **₼38.00/min** across the 27 affected cells.
- Affected premium subscribers: **800**.
- Bank HQ contract (`CT-01`): restore within **180 min**, penalty **₼2,000**
  per started hour over, capped at **₼30,000**. ~20 minutes already elapsed at
  seed time, so ~**2h40min** remains.

## Not yet available (coming in later stages)

- `GET /api/explain/{metric}` — provenance (formula + sources) for any number.
- `GET /api/contracts` — tracker with live compliance state (ok/at risk/breached).
- `POST /api/actions/{id}/approve` / `reject` — role-checked approvals.
- `GET /api/audit` — audit log.
- `GET /api/settings` / `PUT /api/settings` — autonomy level.
- SLA countdown / revenue ticker values (computed, with formula+sources).
