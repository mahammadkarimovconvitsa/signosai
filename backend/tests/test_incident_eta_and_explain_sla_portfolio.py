from datetime import UTC, date, datetime, timedelta

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
    IncidentStatus,
    LinkType,
    OperationalStatus,
    UserRole,
)
from app.models.incident import Incident, IncidentAffectedSite
from app.models.link import Link
from app.models.site import Site
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def _seed_incident_with_contract(db_session: AsyncSession) -> tuple[Incident, Contract, Site]:
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
    cell = Cell(
        site_id=site.id, technology=CellTechnology.FOUR_G,
        revenue_per_min_azn=10, status=OperationalStatus.DOWN,
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
    await db_session.flush()
    incident = Incident(
        root_cause_link_id=link.id, root_cause_summary="Fiber cut",
        status=IncidentStatus.OPEN, started_at=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.flush()
    db_session.add(IncidentAffectedSite(incident_id=incident.id, site_id=site.id))
    await db_session.commit()
    await db_session.refresh(incident)
    await db_session.refresh(contract)
    return incident, contract, site


async def test_update_eta_requires_engineer_or_admin(client: AsyncClient, db_session: AsyncSession):
    incident, _, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.put(
        f"/api/v1/incidents/{incident.id}/eta",
        json={"eta_at": datetime.now(UTC).isoformat()},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_update_eta_success_reflected_in_sla(client: AsyncClient, db_session: AsyncSession):
    incident, contract, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    eta_at = datetime.now(UTC) + timedelta(hours=2)

    resp = await client.put(
        f"/api/v1/incidents/{incident.id}/eta",
        json={"eta_at": eta_at.isoformat()},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["eta_at"] is not None

    resp = await client.get(f"/api/v1/incidents/{incident.id}/timeline", headers=headers)
    assert any(e["label"] == "eta_updated" for e in resp.json())

    resp = await client.get(f"/api/v1/incidents/{incident.id}/sla", headers=headers)
    sla = resp.json()[0]
    assert sla["projected_penalty_at_eta_azn"] is not None


async def test_update_eta_404_for_unknown_incident(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.put(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/eta",
        json={"eta_at": datetime.now(UTC).isoformat()},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_resolve_already_resolved_is_idempotent(
    client: AsyncClient, db_session: AsyncSession
):
    incident, _, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    first = await client.post(f"/api/v1/incidents/{incident.id}/resolve", headers=headers)
    second = await client.post(f"/api/v1/incidents/{incident.id}/resolve", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "resolved"


async def test_resolve_404_for_unknown_incident(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/resolve", headers=headers
    )
    assert resp.status_code == 404


async def test_explain_sla_metric_fields(client: AsyncClient, db_session: AsyncSession):
    incident, contract, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)

    for field in ["deadline", "time_remaining", "penalty_accrued", "worst_case_penalty"]:
        resp = await client.get(
            f"/api/v1/explain/sla.{field}:{incident.id}:{contract.id}", headers=headers
        )
        assert resp.status_code == 200, f"field={field}"
        assert "formula" in resp.json()


async def test_explain_sla_projected_penalty_without_eta_is_404(
    client: AsyncClient, db_session: AsyncSession
):
    incident, contract, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        f"/api/v1/explain/sla.projected_penalty_at_eta:{incident.id}:{contract.id}",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_explain_sla_unknown_contract_404(client: AsyncClient, db_session: AsyncSession):
    incident, _, _ = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        f"/api/v1/explain/sla.deadline:{incident.id}:00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_explain_portfolio_metric_fields(client: AsyncClient, db_session: AsyncSession):
    _, _, site = await _seed_incident_with_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)

    for field in ["traffic", "revenue", "energy_cost", "ratio"]:
        resp = await client.get(f"/api/v1/explain/portfolio.{field}:{site.id}", headers=headers)
        assert resp.status_code == 200, f"field={field}"


async def test_explain_portfolio_unknown_site_404(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        "/api/v1/explain/portfolio.revenue:00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_explain_malformed_sla_id_is_400(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    # Missing the contract_id segment.
    resp = await client.get(
        "/api/v1/explain/sla.deadline:00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 422
