from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.customer import EnterpriseCustomer
from app.models.enums import ContractType, IncidentStatus, LinkType, OperationalStatus
from app.models.incident import Incident, IncidentAffectedSite
from app.models.link import Link
from app.models.site import Site
from app.services.sla_service import SlaService, _penalty_for_hours_over

pytestmark = pytest.mark.asyncio


async def _seed_incident_with_contract(
    db_session: AsyncSession,
    *,
    started_at: datetime,
    restore_within_min: int = 180,
    rate: float = 2000,
    cap: float = 30000,
    eta_at: datetime | None = None,
) -> tuple[Incident, Contract]:
    site = Site(
        name="Bank HQ Site",
        lat=40.4,
        lng=49.8,
        district="Nasimi",
        energy_cost_azn_month=500,
        status=OperationalStatus.DOWN,
    )
    db_session.add(site)
    await db_session.flush()

    link = Link(
        from_site_id=site.id,
        to_site_id=site.id,
        type=LinkType.FIBER,
        is_protected=False,
        status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.flush()

    customer = EnterpriseCustomer(name="Bank HQ", sector="finance")
    db_session.add(customer)
    await db_session.flush()

    contract = Contract(
        customer_id=customer.id,
        type=ContractType.ENTERPRISE_SLA,
        restore_within_min=restore_within_min,
        penalty_per_started_hour_azn=rate,
        penalty_cap_azn=cap,
        clause_text="Restore within window or pay penalty.",
        valid_from=date(2026, 1, 1),
    )
    db_session.add(contract)
    await db_session.flush()

    incident = Incident(
        root_cause_link_id=link.id,
        root_cause_summary="Fiber cut",
        status=IncidentStatus.OPEN,
        started_at=started_at,
        eta_at=eta_at,
    )
    db_session.add(incident)
    await db_session.flush()

    db_session.add(IncidentAffectedSite(incident_id=incident.id, site_id=site.id))
    # No customer_sites row yet — tests that need get_incident_sla() add one.
    await db_session.commit()
    await db_session.refresh(incident)
    await db_session.refresh(contract)
    return incident, contract


@pytest.mark.parametrize(
    "hours_over,rate,cap,expected",
    [
        (0, 2000, 30000, 0),
        (-5, 2000, 30000, 0),
        (0.0001, 2000, 30000, 2000),  # any started hour bills in full
        (1.0, 2000, 30000, 2000),
        (1.5, 2000, 30000, 4000),  # ceil(1.5) = 2
        (2.0, 2000, 30000, 4000),
        (100, 2000, 30000, 30000),  # capped
    ],
)
async def test_penalty_for_hours_over(hours_over, rate, cap, expected):
    assert _penalty_for_hours_over(hours_over, rate, cap) == expected


async def test_compliance_ok_well_before_deadline(db_session: AsyncSession):
    now = datetime.now(UTC)
    incident, contract = await _seed_incident_with_contract(db_session, started_at=now)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.compliance_status.value == "ok"
    assert sla.time_remaining_min.value == pytest.approx(180, abs=0.01)


async def test_compliance_at_risk_boundary(db_session: AsyncSession):
    now = datetime.now(UTC)
    # deadline = started_at + 180min. Set started_at so exactly 60min remain.
    started_at = now - timedelta(minutes=120)
    incident, contract = await _seed_incident_with_contract(db_session, started_at=started_at)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.time_remaining_min.value == pytest.approx(60, abs=0.01)
    assert sla.compliance_status.value == "at_risk"


async def test_compliance_ok_just_above_threshold(db_session: AsyncSession):
    now = datetime.now(UTC)
    started_at = now - timedelta(minutes=119)  # 61 min remain
    incident, contract = await _seed_incident_with_contract(db_session, started_at=started_at)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.compliance_status.value == "ok"


async def test_compliance_breached_at_exact_deadline(db_session: AsyncSession):
    now = datetime.now(UTC)
    started_at = now - timedelta(minutes=180)  # remaining == 0
    incident, contract = await _seed_incident_with_contract(db_session, started_at=started_at)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.time_remaining_min.value == pytest.approx(0, abs=0.01)
    assert sla.compliance_status.value == "breached"


async def test_no_eta_means_no_projected_penalty(db_session: AsyncSession):
    now = datetime.now(UTC)
    incident, contract = await _seed_incident_with_contract(db_session, started_at=now)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.projected_penalty_at_eta_azn is None


async def test_projected_penalty_at_eta(db_session: AsyncSession):
    now = datetime.now(UTC)
    started_at = now - timedelta(minutes=20)
    # deadline = started_at + 180min. eta 1.5h after deadline -> ceil(1.5)=2 -> 2*2000=4000
    eta_at = started_at + timedelta(minutes=180) + timedelta(hours=1, minutes=30)
    incident, contract = await _seed_incident_with_contract(
        db_session, started_at=started_at, eta_at=eta_at
    )
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.projected_penalty_at_eta_azn.value == 4000


async def test_worst_case_penalty_is_always_the_cap(db_session: AsyncSession):
    now = datetime.now(UTC)
    incident, contract = await _seed_incident_with_contract(db_session, started_at=now, cap=30000)
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.worst_case_penalty_azn.value == 30000


async def test_bank_hq_scenario_matches_known_numbers(db_session: AsyncSession):
    """Sanity-check against the exact numbers from the hackathon roadmap doc."""
    now = datetime.now(UTC)
    started_at = now - timedelta(minutes=20)
    incident, contract = await _seed_incident_with_contract(
        db_session, started_at=started_at, restore_within_min=180, rate=2000, cap=30000
    )
    sla = await SlaService(db_session).get_contract_sla(incident.id, contract, now=now)
    assert sla.time_remaining_min.value == pytest.approx(160, abs=0.1)  # ~2h40min
