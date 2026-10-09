from uuid import UUID

from sqlalchemy import select

from app.models.enums import SubscriberSegment
from app.models.subscriber import Subscriber, SubscriberSegmentCount
from app.repositories.base import BaseRepository


class SubscriberRepository(BaseRepository):
    async def list_segment_counts_for_cells(
        self, cell_ids: list[UUID], segment: SubscriberSegment | None = None
    ) -> list[SubscriberSegmentCount]:
        if not cell_ids:
            return []
        stmt = select(SubscriberSegmentCount).where(SubscriberSegmentCount.cell_id.in_(cell_ids))
        if segment is not None:
            stmt = stmt.where(SubscriberSegmentCount.segment == segment)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_named_subscribers_for_cells(
        self, cell_ids: list[UUID], segment: SubscriberSegment | None = None, limit: int = 1000
    ) -> list[Subscriber]:
        if not cell_ids:
            return []
        stmt = select(Subscriber).where(Subscriber.home_cell_id.in_(cell_ids))
        if segment is not None:
            stmt = stmt.where(Subscriber.segment == segment)
        result = await self.db.execute(stmt.limit(limit))
        return list(result.scalars().all())
