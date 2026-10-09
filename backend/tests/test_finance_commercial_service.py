from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_config import BusinessConfig
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
    SubscriberSegment,
)
from app.models.incident import Incident, IncidentAffectedSite
from app.models.link import Link
from app.models.site import Site
from app.models.subscriber import Subscriber, SubscriberSegmentCount
from app.services.commercial_service import CommercialService
from app.services.finance_service import FinanceService

pytestmark = pytest.mark.asyncio


async def _seed_full_scenario(db_session: AsyncSession, *, eta_at: datetime | None = None):
    """Mirrors the roadmap's FL-07 / Bank HQ demo scenario at a small scale."""
    hub = Site(
        name="Hub",
        lat=40.4,
        lng=49.8,
        district="Nasimi",
        energy_cost_azn_month=500,
        status=OperationalStatus.UP,
    )
    db_session.add(hub)
    await db_session.flush()

    link = Link(
        from_site_id=hub.id,
        to_site_id=hub.id,
        type=LinkType.FIBER,
        is_protected=False,
        status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.flush()

    site = Site(
        name="Affected Site",
        lat=40.45,
        lng=49.78,
        district="Binagadi",
        uplink_link_id=link.id,
        energy_cost_azn_month=1000,
        status=OperationalStatus.DOWN,
    )
    db_session.add(site)
    await db_session.flush()

    cell_a = Cell(
        site_id=site.id,
        technology=CellTechnology.FOUR_G,
        revenue_per_min_azn=10,
        status=OperationalStatus.DOWN,
    )
    cell_b = Cell(
        site_id=site.id,
        technology=CellTechnology.FIVE_G,
        revenue_per_min_azn=28,
        status=OperationalStatus.DOWN,
    )
    db_session.add_all([cell_a, cell_b])
    await db_session.flush()

    premium_segment = SubscriberSegmentCount(
        cell_id=cell_a.id, segment=SubscriberSegment.PREMIUM, count=500, arpu_azn=50
    )
    premium_segment_b = SubscriberSegmentCount(
        cell_id=cell_b.id, segment=SubscriberSegment.PREMIUM, count=300, arpu_azn=50
    )
    standard_segment = SubscriberSegmentCount(
        cell_id=cell_a.id, segment=SubscriberSegment.STANDARD, count=1000, arpu_azn=20
    )
    db_session.add_all([premium_segment, premium_segment_b, standard_segment])

    named_subscriber = Subscriber(
        home_cell_id=cell_a.id,
        segment=SubscriberSegment.PREMIUM,
        msisdn_masked="+994 XX XXX 01",
        name="Ada Lovelace",
    )
    db_session.add(named_subscriber)

    customer = EnterpriseCustomer(name="Bank HQ", sector="finance")
    db_session.add(customer)
    await db_session.flush()

    db_session.add(
        CustomerSite(
            customer_id=customer.id,
            site_id=site.id,
            service_type=CustomerServiceType.LEASED_LINE,
        )
    )

    started_at = datetime.now(UTC) - timedelta(minutes=20)
    contract = Contract(
        customer_id=customer.id,
        type=ContractType.ENTERPRISE_SLA,
        restore_within_min=180,
        penalty_per_started_hour_azn=2000,
        penalty_cap_azn=30000,
        clause_text="Restore within 3 hours.",
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
    await db_session.commit()
    await db_session.refresh(incident)
    return incident


async def test_revenue_per_min_sums_affected_cells(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    metric = await FinanceService(db_session).get_revenue_per_min(incident.id)
    assert metric.value == pytest.approx(38.0)  # 10 + 28, matches the roadmap's ₼38/min


async def test_affected_premium_subscriber_count(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    metric = await CommercialService(db_session).get_affected_premium_count(incident.id)
    assert metric.value == 800  # 500 + 300, matches the roadmap's 800 premium subs


async def test_compensation_cost_uses_default_rate(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    metric = await CommercialService(db_session).get_compensation_cost(incident.id)
    assert metric.value == pytest.approx(800 * 2.0)  # default ₼2/subscriber


async def test_compensation_cost_uses_business_config_override(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    db_session.add(BusinessConfig(key="compensation_per_subscriber_azn", value="5.0"))
    await db_session.commit()
    metric = await CommercialService(db_session).get_compensation_cost(incident.id)
    assert metric.value == pytest.approx(800 * 5.0)


async def test_sample_subscribers_only_premium(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    samples = await CommercialService(db_session).get_sample_subscribers(incident.id)
    assert len(samples) == 1
    assert samples[0].name == "Ada Lovelace"


async def test_lost_revenue_without_eta_uses_now(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    now = incident.started_at + timedelta(minutes=10)
    metric = await FinanceService(db_session).get_lost_revenue(incident.id, now=now)
    assert metric.value == pytest.approx(38.0 * 10)


async def test_lost_revenue_with_eta_uses_eta(db_session: AsyncSession):
    eta_at = datetime.now(UTC) + timedelta(hours=2)
    incident = await _seed_full_scenario(db_session, eta_at=eta_at)
    now = datetime.now(UTC)
    metric = await FinanceService(db_session).get_lost_revenue(incident.id, now=now)
    expected_minutes = (eta_at - incident.started_at).total_seconds() / 60
    assert metric.value == pytest.approx(38.0 * expected_minutes, rel=1e-3)


async def test_total_exposure_is_sum_of_components(db_session: AsyncSession):
    incident = await _seed_full_scenario(db_session)
    now = datetime.now(UTC)
    summary = await FinanceService(db_session).get_summary(incident.id, now=now)
    expected = (
        summary.lost_revenue_azn.value
        + summary.projected_penalties_azn.value
        + summary.compensation_cost_azn.value
    )
    assert summary.total_exposure_azn.value == pytest.approx(expected)
