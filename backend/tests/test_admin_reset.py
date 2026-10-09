from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.alarm import Alarm
from app.models.enums import (
    ActionAgent,
    ActionStatus,
    AlarmSeverity,
    IncidentStatus,
    LinkType,
    OperationalStatus,
    RiskLevel,
    UserRole,
)
from app.models.incident import Incident
from app.models.link import Link
from app.models.site import Site
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def _seed_operational_state(db_session: AsyncSession):
    site = Site(
        name="S", lat=40.4, lng=49.8, district="Nasimi",
        energy_cost_azn_month=500, status=OperationalStatus.DOWN,
    )
    db_session.add(site)
    await db_session.flush()
    link = Link(
        from_site_id=site.id, to_site_id=site.id, type=LinkType.FIBER,
        is_protected=False, status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.flush()
    incident = Incident(
        root_cause_link_id=link.id, root_cause_summary="Fiber cut",
        status=IncidentStatus.OPEN, started_at=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.flush()
    db_session.add(
        Action(
            incident_id=incident.id, agent=ActionAgent.NETWORK, proposal="x",
            owner_role=UserRole.ENGINEER, status=ActionStatus.PROPOSED,
            risk_level=RiskLevel.LOW, sources=[],
        )
    )
    # An alarm linked to the incident -- this FK is what caught the real
    # delete-order bug found during live testing (alarms must be deleted
    # before incidents, not after).
    db_session.add(
        Alarm(
            timestamp=datetime.now(UTC), site_id=site.id, severity=AlarmSeverity.CRITICAL,
            type="link_down", processed=True, incident_id=incident.id,
        )
    )
    await db_session.commit()
    return site, link, incident


async def test_reset_requires_admin(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post("/api/v1/admin/reset", headers=headers)
    assert resp.status_code == 403


async def test_reset_clears_operational_data_and_restores_statuses(
    client: AsyncClient, db_session: AsyncSession
):
    site, link, incident = await _seed_operational_state(db_session)
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)

    resp = await client.post("/api/v1/admin/reset", headers=headers)
    assert resp.status_code == 204

    resp = await client.get("/api/v1/incidents", headers=headers)
    assert resp.json()["total"] == 0

    resp = await client.get("/api/v1/actions", headers=headers)
    assert resp.json()["total"] == 0

    resp = await client.get(f"/api/v1/network/sites/{site.id}", headers=headers)
    assert resp.json()["status"] == "up"

    resp = await client.get("/api/v1/network/links", headers=headers)
    assert all(link_out["status"] == "up" for link_out in resp.json()["items"])

    resp = await client.get("/api/v1/audit", headers=headers, params={"entity": "system"})
    events = resp.json()["items"]
    assert any(e["event_type"] == "admin.reset" for e in events)
