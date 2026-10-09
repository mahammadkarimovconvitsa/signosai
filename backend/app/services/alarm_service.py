from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm
from app.repositories.alarm_repository import AlarmRepository
from app.schemas.alarm import AlarmIn, AlarmIngestResult
from app.services.correlation_service import CorrelationService


class AlarmService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alarms = AlarmRepository(db)

    async def ingest(self, alarms_in: list[AlarmIn]) -> AlarmIngestResult:
        await self.alarms.create_many([a.model_dump() for a in alarms_in])
        await self.db.commit()

        incident = await CorrelationService(self.db).correlate()
        return AlarmIngestResult(
            ingested=len(alarms_in), incident_id=incident.id if incident else None
        )

    async def list_alarms(
        self, limit: int, offset: int, *, processed: bool | None = None, site_id: UUID | None = None
    ) -> tuple[list[Alarm], int]:
        return await self.alarms.list_paginated(limit, offset, processed=processed, site_id=site_id)
