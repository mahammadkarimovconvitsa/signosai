from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm
from app.models.enums import AlarmSeverity, LinkType, OperationalStatus
from app.models.link import Link
from app.models.site import Site
from app.services.correlation_service import CorrelationService

pytestmark = pytest.mark.asyncio


async def _make_site(db_session: AsyncSession, name: str, uplink_link_id=None, **kwargs) -> Site:
    site = Site(
        name=name,
        lat=40.4,
        lng=49.8,
        district="Nasimi",
        uplink_link_id=uplink_link_id,
        energy_cost_azn_month=500,
        status=OperationalStatus.UP,
        **kwargs,
    )
    db_session.add(site)
    await db_session.flush()
    return site


async def _make_link(
    db_session: AsyncSession, from_site: Site, to_site: Site, is_protected: bool = False
) -> Link:
    link = Link(
        from_site_id=from_site.id,
        to_site_id=to_site.id,
        type=LinkType.FIBER,
        is_protected=is_protected,
        status=OperationalStatus.UP,
    )
    db_session.add(link)
    await db_session.flush()
    return link


async def _make_alarm(db_session: AsyncSession, site: Site, ts: datetime | None = None) -> Alarm:
    alarm = Alarm(
        timestamp=ts or datetime.now(UTC),
        site_id=site.id,
        severity=AlarmSeverity.CRITICAL,
        type="link_down",
        processed=False,
    )
    db_session.add(alarm)
    await db_session.flush()
    return alarm


async def test_no_unprocessed_alarms_returns_none(db_session: AsyncSession):
    incident = await CorrelationService(db_session).correlate()
    assert incident is None


async def test_basic_correlation_creates_incident(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    link = await _make_link(db_session, hub, hub)
    # 3 downstream sites all fed by the same link
    downstream = [
        await _make_site(db_session, f"Downstream {i}", uplink_link_id=link.id) for i in range(3)
    ]
    for site in downstream:
        await _make_alarm(db_session, site)
    await db_session.commit()

    incident = await CorrelationService(db_session).correlate()

    assert incident is not None
    assert incident.root_cause_link_id == link.id
    assert incident.status.value == "open"

    await db_session.refresh(link)
    assert link.status == OperationalStatus.DOWN
    for site in downstream:
        await db_session.refresh(site)
        assert site.status == OperationalStatus.DOWN


async def test_affected_sites_include_non_alarming_siblings(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    link = await _make_link(db_session, hub, hub)
    alarming_site = await _make_site(db_session, "Alarming", uplink_link_id=link.id)
    silent_sibling = await _make_site(db_session, "Silent sibling", uplink_link_id=link.id)
    await _make_alarm(db_session, alarming_site)
    await db_session.commit()

    from app.repositories.incident_repository import IncidentRepository

    incident = await CorrelationService(db_session).correlate()
    affected = await IncidentRepository(db_session).list_affected_sites(incident.id)
    affected_site_ids = {a.site_id for a in affected}

    assert alarming_site.id in affected_site_ids
    assert silent_sibling.id in affected_site_ids


async def test_protected_link_is_never_root_cause(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    protected_link = await _make_link(db_session, hub, hub, is_protected=True)
    site = await _make_site(db_session, "Behind protected link", uplink_link_id=protected_link.id)
    await _make_alarm(db_session, site)
    await db_session.commit()

    incident = await CorrelationService(db_session).correlate()

    assert incident is None


async def test_dominant_link_wins_over_smaller_cluster(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    big_link = await _make_link(db_session, hub, hub)
    small_link = await _make_link(db_session, hub, hub)

    big_cluster = [
        await _make_site(db_session, f"Big {i}", uplink_link_id=big_link.id) for i in range(3)
    ]
    small_cluster = [await _make_site(db_session, "Small 0", uplink_link_id=small_link.id)]

    for site in big_cluster + small_cluster:
        await _make_alarm(db_session, site)
    await db_session.commit()

    incident = await CorrelationService(db_session).correlate()

    assert incident.root_cause_link_id == big_link.id


async def test_second_correlate_call_reuses_open_incident(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    link = await _make_link(db_session, hub, hub)
    site_a = await _make_site(db_session, "A", uplink_link_id=link.id)
    await _make_alarm(db_session, site_a)
    await db_session.commit()

    service = CorrelationService(db_session)
    first = await service.correlate()

    site_b = await _make_site(db_session, "B", uplink_link_id=link.id)
    await _make_alarm(db_session, site_b)
    await db_session.commit()

    second = await service.correlate()

    assert second.id == first.id

    from app.repositories.incident_repository import IncidentRepository

    affected = await IncidentRepository(db_session).list_affected_sites(second.id)
    assert len({a.site_id for a in affected}) == 2


async def test_started_at_uses_earliest_alarm_timestamp(db_session: AsyncSession):
    hub = await _make_site(db_session, "Hub")
    link = await _make_link(db_session, hub, hub)
    site = await _make_site(db_session, "A", uplink_link_id=link.id)
    early = datetime.now(UTC) - timedelta(minutes=20)
    await _make_alarm(db_session, site, ts=early)
    await _make_alarm(db_session, site, ts=datetime.now(UTC))
    await db_session.commit()

    incident = await CorrelationService(db_session).correlate()

    assert abs((incident.started_at - early).total_seconds()) < 1
