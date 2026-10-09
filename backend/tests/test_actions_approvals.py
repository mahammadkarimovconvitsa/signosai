from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.enums import (
    ActionAgent,
    ActionStatus,
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


async def _seed_action(db_session: AsyncSession, owner_role: UserRole) -> Action:
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

    action = Action(
        incident_id=incident.id,
        agent=ActionAgent.NETWORK,
        proposal="Dispatch field crew",
        owner_role=owner_role,
        status=ActionStatus.PROPOSED,
        risk_level=RiskLevel.MEDIUM,
        sources=[{"table": "links", "id": str(link.id)}],
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)
    return action


async def test_list_actions_filtered_by_role(client: AsyncClient, db_session: AsyncSession):
    await _seed_action(db_session, UserRole.ENGINEER)
    await _seed_action(db_session, UserRole.ACCOUNT_MANAGER)

    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.get("/api/v1/actions", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["owner_role"] == "engineer"


async def test_admin_sees_all_actions(client: AsyncClient, db_session: AsyncSession):
    await _seed_action(db_session, UserRole.ENGINEER)
    await _seed_action(db_session, UserRole.ACCOUNT_MANAGER)

    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.get("/api/v1/actions", headers=headers)
    assert resp.json()["total"] == 2


async def test_approve_requires_matching_role(client: AsyncClient, db_session: AsyncSession):
    action = await _seed_action(db_session, UserRole.ACCOUNT_MANAGER)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    assert resp.status_code == 403


async def test_approve_by_owner_role_succeeds(client: AsyncClient, db_session: AsyncSession):
    action = await _seed_action(db_session, UserRole.ENGINEER)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["approved_by_user_id"] is not None


async def test_admin_can_approve_any_action(client: AsyncClient, db_session: AsyncSession):
    action = await _seed_action(db_session, UserRole.ACCOUNT_MANAGER)
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    assert resp.status_code == 200


async def test_double_approve_is_idempotent(client: AsyncClient, db_session: AsyncSession):
    action = await _seed_action(db_session, UserRole.ENGINEER)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    first = await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    second = await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["approved_at"] == second.json()["approved_at"]


async def test_reject_after_approve_conflicts(client: AsyncClient, db_session: AsyncSession):
    action = await _seed_action(db_session, UserRole.ENGINEER)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    await client.post(f"/api/v1/actions/{action.id}/approve", headers=headers)
    resp = await client.post(f"/api/v1/actions/{action.id}/reject", headers=headers)
    assert resp.status_code == 409
