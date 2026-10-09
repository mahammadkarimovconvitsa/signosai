from uuid import UUID

from sqlalchemy import select, update

from app.models.alarm import Alarm
from app.repositories.base import BaseRepository


class AlarmRepository(BaseRepository):
    async def list_unprocessed(self) -> list[Alarm]:
        result = await self.db.execute(select(Alarm).where(Alarm.processed.is_(False)))
        return list(result.scalars().all())

    async def create_many(self, alarms: list[dict]) -> list[Alarm]:
        rows = [Alarm(**data) for data in alarms]
        self.db.add_all(rows)
        await self.db.flush()
        return rows

    async def mark_processed(self, alarm_ids: list[UUID], incident_id: UUID) -> None:
        if not alarm_ids:
            return
        stmt = (
            update(Alarm)
            .where(Alarm.id.in_(alarm_ids))
            .values(processed=True, incident_id=incident_id)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def list_paginated(
        self, limit: int, offset: int, *, processed: bool | None = None, site_id: UUID | None = None
    ) -> tuple[list[Alarm], int]:
        stmt = select(Alarm).order_by(Alarm.timestamp.desc())
        if processed is not None:
            stmt = stmt.where(Alarm.processed.is_(processed))
        if site_id is not None:
            stmt = stmt.where(Alarm.site_id == site_id)
        return await self.paginate(stmt, limit, offset)

    async def list_for_incident(self, incident_id: UUID) -> list[Alarm]:
        result = await self.db.execute(select(Alarm).where(Alarm.incident_id == incident_id))
        return list(result.scalars().all())
