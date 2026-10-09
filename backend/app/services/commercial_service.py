from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SubscriberSegment
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.commercial import CommercialSummaryOut, SubscriberOut
from app.schemas.metric import Metric, SourceRef
from app.services.config_service import ConfigService
from app.services.impact_service import ImpactService

DEFAULT_COMPENSATION_PER_SUBSCRIBER_AZN = "2.0"


class CommercialService:
    def __init__(self, db: AsyncSession):
        self.impact = ImpactService(db)
        self.subscribers = SubscriberRepository(db)
        self.config = ConfigService(db)

    async def get_affected_premium_count(self, incident_id: UUID) -> Metric:
        cells = await self.impact.get_affected_cells(incident_id)
        cell_ids = [c.id for c in cells]
        segment_counts = await self.subscribers.list_segment_counts_for_cells(
            cell_ids, segment=SubscriberSegment.PREMIUM
        )
        total = sum(sc.count for sc in segment_counts)
        return Metric(
            value=total,
            unit="subscribers",
            formula="sum(subscriber_segments.count where segment='premium' for affected cells)",
            inputs={"affected_cell_count": len(cell_ids)},
            sources=[
                SourceRef(table="subscriber_segments", id=str(sc.id)) for sc in segment_counts
            ],
        )

    async def get_compensation_cost(self, incident_id: UUID) -> Metric:
        premium_count = await self.get_affected_premium_count(incident_id)
        per_subscriber = float(
            await self.config.get_value(
                "compensation_per_subscriber_azn", DEFAULT_COMPENSATION_PER_SUBSCRIBER_AZN
            )
        )
        cost = premium_count.value * per_subscriber
        return Metric(
            value=cost,
            unit="AZN",
            formula="affected_premium_subscribers * compensation_per_subscriber_azn",
            inputs={
                "affected_premium_subscribers": premium_count.value,
                "compensation_per_subscriber_azn": per_subscriber,
            },
            sources=premium_count.sources,
        )

    async def get_sample_subscribers(
        self, incident_id: UUID, limit: int = 50
    ) -> list[SubscriberOut]:
        cells = await self.impact.get_affected_cells(incident_id)
        subscribers = await self.subscribers.list_named_subscribers_for_cells(
            [c.id for c in cells], segment=SubscriberSegment.PREMIUM, limit=limit
        )
        return [SubscriberOut.model_validate(s) for s in subscribers]

    async def get_summary(self, incident_id: UUID) -> CommercialSummaryOut:
        premium_count = await self.get_affected_premium_count(incident_id)
        compensation_cost = await self.get_compensation_cost(incident_id)
        sample = await self.get_sample_subscribers(incident_id)
        return CommercialSummaryOut(
            incident_id=incident_id,
            affected_premium_subscribers=premium_count,
            compensation_cost_azn=compensation_cost,
            sample_subscribers=sample,
        )
