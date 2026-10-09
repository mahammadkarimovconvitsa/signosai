from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site
from app.repositories.network_repository import CellRepository, SiteRepository
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.metric import Metric, SourceRef
from app.schemas.portfolio import PortfolioRecommendation, SitePortfolioOut
from app.services.config_service import ConfigService

MINUTES_PER_30_DAY_MONTH = 30 * 24 * 60

DEFAULT_UPGRADE_RATIO_THRESHOLD = "3.0"
DEFAULT_UPGRADE_TRAFFIC_THRESHOLD = "200"
DEFAULT_KEEP_RATIO_THRESHOLD = "1.0"
DEFAULT_CONSOLIDATE_RATIO_THRESHOLD = "0.3"


class PortfolioService:
    """Deterministic site recommendation: revenue-to-energy-cost ratio + traffic.

    Monthly revenue is a simplified projection (per-minute cell revenue x a
    30-day month at full theoretical utilization) — a deliberate simplification
    documented here and in docs/DATA_SCHEMA.md, not a real utilization model.
    Traffic is approximated as total subscribers served by the site's cells,
    since the schema has no dedicated traffic/usage metric.
    """

    def __init__(self, db: AsyncSession):
        self.sites = SiteRepository(db)
        self.cells = CellRepository(db)
        self.subscribers = SubscriberRepository(db)
        self.config = ConfigService(db)

    async def get_site_portfolio(self, site: Site) -> SitePortfolioOut:
        cells = await self.cells.list_for_sites([site.id])
        cell_ids = [c.id for c in cells]

        revenue_per_min_total = sum(float(c.revenue_per_min_azn) for c in cells)
        monthly_revenue = revenue_per_min_total * MINUTES_PER_30_DAY_MONTH

        segment_counts = await self.subscribers.list_segment_counts_for_cells(cell_ids)
        traffic = sum(sc.count for sc in segment_counts)

        energy_cost = float(site.energy_cost_azn_month)
        ratio = monthly_revenue / max(energy_cost, 0.01)

        recommendation = await self._recommend(ratio, traffic)

        cell_sources = [SourceRef(table="cells", id=str(c.id)) for c in cells]

        return SitePortfolioOut(
            site_id=site.id,
            site_name=site.name,
            traffic_proxy_subscribers=Metric(
                value=traffic,
                unit="subscribers",
                formula="sum(subscriber_segments.count for site's cells)",
                inputs={"cell_count": len(cells)},
                sources=[
                    SourceRef(table="subscriber_segments", id=str(sc.id)) for sc in segment_counts
                ],
            ),
            revenue_azn_month=Metric(
                value=monthly_revenue,
                unit="AZN/month",
                formula="sum(cell.revenue_per_min_azn) * minutes in a 30-day month",
                inputs={
                    "revenue_per_min_azn_total": revenue_per_min_total,
                    "minutes_per_month": MINUTES_PER_30_DAY_MONTH,
                },
                sources=cell_sources,
            ),
            energy_cost_azn_month=Metric(
                value=energy_cost,
                unit="AZN/month",
                formula="site.energy_cost_azn_month",
                inputs={},
                sources=[SourceRef(table="sites", id=str(site.id))],
            ),
            revenue_to_cost_ratio=Metric(
                value=ratio,
                unit="ratio",
                formula="revenue_azn_month / energy_cost_azn_month",
                inputs={"revenue_azn_month": monthly_revenue, "energy_cost_azn_month": energy_cost},
                sources=cell_sources + [SourceRef(table="sites", id=str(site.id))],
            ),
            recommendation=recommendation,
        )

    async def list_portfolio(self, limit: int, offset: int) -> tuple[list[SitePortfolioOut], int]:
        sites, total = await self.sites.list_paginated(limit, offset)
        return [await self.get_site_portfolio(s) for s in sites], total

    async def _recommend(self, ratio: float, traffic: int) -> PortfolioRecommendation:
        upgrade_ratio = float(
            await self.config.get_value(
                "portfolio_upgrade_ratio_threshold", DEFAULT_UPGRADE_RATIO_THRESHOLD
            )
        )
        upgrade_traffic = float(
            await self.config.get_value(
                "portfolio_upgrade_traffic_threshold", DEFAULT_UPGRADE_TRAFFIC_THRESHOLD
            )
        )
        keep_ratio = float(
            await self.config.get_value(
                "portfolio_keep_ratio_threshold", DEFAULT_KEEP_RATIO_THRESHOLD
            )
        )
        consolidate_ratio = float(
            await self.config.get_value(
                "portfolio_consolidate_ratio_threshold", DEFAULT_CONSOLIDATE_RATIO_THRESHOLD
            )
        )

        if ratio >= upgrade_ratio and traffic >= upgrade_traffic:
            return PortfolioRecommendation.UPGRADE
        if ratio >= keep_ratio:
            return PortfolioRecommendation.KEEP
        if ratio >= consolidate_ratio:
            return PortfolioRecommendation.CONSOLIDATE
        return PortfolioRecommendation.DECOMMISSION
