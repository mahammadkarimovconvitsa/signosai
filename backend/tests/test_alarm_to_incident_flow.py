from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cell import Cell
from app.models.contract import Contract
from app.models.customer import CustomerSite, EnterpriseCustomer
from app.models.enums import (
    CellTechnology,
    ContractType,
    CustomerServiceType,
    LinkType,
    OperationalStatus,
    UserRole,
)
from app.models.link import Link
from app.models.site import Site
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def _seed_topology(db_session: AsyncSession) -> dict:
    hub = Site(
        name="Nasimi Hub", lat=40.4, lng=49.8, district="Nasimi",
        energy_cost_azn_month=500, status=OperationalStatus.UP,
    )
    db_session.add(hub)
    await db_session.flush()

    link = Link(
        from_site_id=hub.id, to_site_id=hub.id, type=LinkType.FIBER,
        is_protected=False, status=OperationalStatus.UP,
    )
    db_session.add(link)
    await db_session.flush()

    site = Site(
        name="Binagadi Site 1", lat=40.45, lng=49.78, district="Binagadi",
        uplink_link_id=link.id, energy_cost_azn_month=620, status=OperationalStatus.UP,
    )
    db_session.add(site)
    await db_session.flush()

    cell = Cell(
        site_id=site.id, technology=CellTechnology.FOUR_G,
        revenue_per_min_azn=38, status=OperationalStatus.UP,
    )
    db_session.add(cell)

    customer = EnterpriseCustomer(name="Bank HQ", sector="finance")
    db_session.add(customer)
    await db_session.flush()

    db_session.add(
        CustomerSite(
            customer_id=customer.id, site_id=site.id, service_type=CustomerServiceType.LEASED_LINE
        )
    )

    contract = Contract(
        customer_id=customer.id, type=ContractType.ENTERPRISE_SLA,
        restore_within_min=180, penalty_per_started_hour_azn=2000, penalty_cap_azn=30000,
        clause_text="Restore within 3 hours.", valid_from=date(2026, 1, 1),
    )
    db_session.add(contract)
    await db_session.commit()

    return {"site": site, "link": link, "customer": customer, "contract": contract}


async def test_full_alarm_to_incident_flow(client: AsyncClient, db_session: AsyncSession):
    topology = await _seed_topology(db_session)
    site = topology["site"]

    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)

    # 1. Ingest a batch of alarms for the affected site.
    now = datetime.now(UTC).isoformat()
    resp = await client.post(
        "/api/v1/alarms/ingest",
        json={
            "alarms": [
                {
                    "timestamp": now,
                    "site_id": str(site.id),
                    "severity": "critical",
                    "type": "link_down",
                }
                for _ in range(5)
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ingested"] == 5
    assert body["incident_id"] is not None
    incident_id = body["incident_id"]

    # 2. The current active incident should be this one.
    resp = await client.get("/api/v1/incidents/current", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == incident_id
    assert resp.json()["alarm_count"] == 5
    assert len(resp.json()["affected_sites"]) == 1

    # 3. Site should now be marked down.
    resp = await client.get(f"/api/v1/network/sites/{site.id}", headers=headers)
    assert resp.json()["status"] == "down"

    # 4. Timeline should show the correlation events.
    resp = await client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=headers)
    labels = [e["label"] for e in resp.json()]
    assert "alarms_received" in labels
    assert "correlated" in labels

    # 5. Impact: the bank customer and its contract should show up.
    resp = await client.get(f"/api/v1/incidents/{incident_id}/impact", headers=headers)
    assert resp.status_code == 200
    impact = resp.json()
    assert len(impact) == 1
    assert impact[0]["customer"]["name"] == "Bank HQ"
    assert len(impact[0]["contracts"]) == 1
    assert impact[0]["contracts"][0]["compliance_status"] == "ok"

    # 6. SLA numbers directly.
    resp = await client.get(f"/api/v1/incidents/{incident_id}/sla", headers=headers)
    sla = resp.json()[0]
    assert sla["time_remaining_min"]["value"] == pytest.approx(180, abs=1)

    # 7. Finance: revenue lost per minute matches the single cell.
    resp = await client.get(f"/api/v1/incidents/{incident_id}/finance", headers=headers)
    finance = resp.json()
    assert finance["revenue_per_min_azn"]["value"] == pytest.approx(38.0)

    # 8. Explain: re-derive the same total exposure figure via the explain endpoint.
    # total_exposure ticks live with elapsed time, so the two calls (each with
    # its own "now") won't match to the penny -- just check they're in the same
    # ballpark (well within a second's worth of revenue drift).
    resp = await client.get(
        f"/api/v1/explain/finance.total_exposure:{incident_id}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == pytest.approx(finance["total_exposure_azn"]["value"], abs=1.0)

    # 9. Resolve the incident -- site goes back up, status flips.
    resp = await client.post(f"/api/v1/incidents/{incident_id}/resolve", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"

    resp = await client.get(f"/api/v1/network/sites/{site.id}", headers=headers)
    assert resp.json()["status"] == "up"

    resp = await client.get("/api/v1/incidents/current", headers=headers)
    assert resp.status_code == 404  # no active incident anymore


async def test_ingest_for_site_without_uplink_returns_no_incident(
    client: AsyncClient, db_session: AsyncSession
):
    # A site with no uplink_link_id can never be explained by a failed link.
    orphan_site = Site(
        name="Orphan Site", lat=40.3, lng=49.7, district="Sabail",
        energy_cost_azn_month=300, status=OperationalStatus.UP,
    )
    db_session.add(orphan_site)
    await db_session.commit()

    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post(
        "/api/v1/alarms/ingest",
        json={
            "alarms": [
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "site_id": str(orphan_site.id),
                    "severity": "warning",
                    "type": "noise",
                }
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["incident_id"] is None


async def test_ingest_requires_engineer_or_admin(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.post(
        "/api/v1/alarms/ingest",
        json={"alarms": []},
        headers=headers,
    )
    assert resp.status_code == 403
