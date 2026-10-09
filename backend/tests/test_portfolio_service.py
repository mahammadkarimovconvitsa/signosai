import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_config import BusinessConfig
from app.models.cell import Cell
from app.models.enums import CellTechnology, OperationalStatus, SubscriberSegment
from app.models.site import Site
from app.models.subscriber import SubscriberSegmentCount
from app.services.portfolio_service import MINUTES_PER_30_DAY_MONTH, PortfolioService

pytestmark = pytest.mark.asyncio


async def _make_site_with_cell(
    db_session: AsyncSession, *, revenue_per_min: float, energy_cost: float
) -> Site:
    site = Site(
        name="Test Site",
        lat=40.4,
        lng=49.8,
        district="Nasimi",
        energy_cost_azn_month=energy_cost,
        status=OperationalStatus.UP,
    )
    db_session.add(site)
    await db_session.flush()
    cell = Cell(
        site_id=site.id,
        technology=CellTechnology.FOUR_G,
        revenue_per_min_azn=revenue_per_min,
        status=OperationalStatus.UP,
    )
    db_session.add(cell)
    await db_session.commit()
    await db_session.refresh(site)
    return site


async def test_high_ratio_and_traffic_recommends_upgrade(db_session: AsyncSession):
    # revenue/min 10 -> monthly = 10 * 43200 = 432000; energy 1000 -> ratio 432
    site = await _make_site_with_cell(db_session, revenue_per_min=10, energy_cost=1000)
    cell = (await db_session.execute(select(Cell).where(Cell.site_id == site.id))).scalar_one()
    db_session.add(
        SubscriberSegmentCount(
            cell_id=cell.id, segment=SubscriberSegment.PREMIUM, count=500, arpu_azn=50
        )
    )
    await db_session.commit()

    out = await PortfolioService(db_session).get_site_portfolio(site)
    assert out.recommendation.value == "upgrade"


async def test_high_ratio_low_traffic_recommends_keep_not_upgrade(db_session: AsyncSession):
    site = await _make_site_with_cell(db_session, revenue_per_min=10, energy_cost=1000)
    out = await PortfolioService(db_session).get_site_portfolio(site)
    # ratio is huge (432) but traffic is 0 -> below upgrade_traffic_threshold -> keep
    assert out.recommendation.value == "keep"


async def test_low_ratio_recommends_decommission(db_session: AsyncSession):
    # revenue/min 0.001 -> monthly ~43.2; energy 10000 -> ratio ~0.0043
    site = await _make_site_with_cell(db_session, revenue_per_min=0.001, energy_cost=10000)
    out = await PortfolioService(db_session).get_site_portfolio(site)
    assert out.recommendation.value == "decommission"


async def test_mid_ratio_recommends_consolidate(db_session: AsyncSession):
    # monthly = 1 * 43200 = 43200; energy 100000 -> ratio 0.432 -> between 0.3 and 1.0
    site = await _make_site_with_cell(db_session, revenue_per_min=1, energy_cost=100000)
    out = await PortfolioService(db_session).get_site_portfolio(site)
    assert out.recommendation.value == "consolidate"


async def test_revenue_formula_is_exact(db_session: AsyncSession):
    site = await _make_site_with_cell(db_session, revenue_per_min=2, energy_cost=1000)
    out = await PortfolioService(db_session).get_site_portfolio(site)
    assert out.revenue_azn_month.value == pytest.approx(2 * MINUTES_PER_30_DAY_MONTH)


async def test_thresholds_respect_business_config_override(db_session: AsyncSession):
    site = await _make_site_with_cell(db_session, revenue_per_min=10, energy_cost=1000)
    # ratio 432 would normally be "keep" (no traffic) -- lower the keep threshold
    # so it still clears consolidate, and raise consolidate threshold way up to
    # force decommission, proving the DB value overrides the code default.
    db_session.add(BusinessConfig(key="portfolio_keep_ratio_threshold", value="99999"))
    db_session.add(BusinessConfig(key="portfolio_consolidate_ratio_threshold", value="99999"))
    await db_session.commit()

    out = await PortfolioService(db_session).get_site_portfolio(site)
    assert out.recommendation.value == "decommission"
