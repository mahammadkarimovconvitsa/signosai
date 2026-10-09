from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models.enums import IncidentStatus
from app.models.incident import Incident, IncidentAffectedSite, IncidentTimelineEvent
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository):
    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        return await self.db.get(Incident, incident_id)

    async def get_open_by_root_cause_link(self, link_id: UUID) -> Incident | None:
        stmt = select(Incident).where(
            Incident.root_cause_link_id == link_id, Incident.status == IncidentStatus.OPEN
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_current_active(self) -> Incident | None:
        stmt = (
            select(Incident)
            .where(Incident.status == IncidentStatus.OPEN)
            .order_by(Incident.started_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self, limit: int, offset: int, *, status: IncidentStatus | None = None
    ) -> tuple[list[Incident], int]:
        stmt = select(Incident).order_by(Incident.started_at.desc())
        if status is not None:
            stmt = stmt.where(Incident.status == status)
        return await self.paginate(stmt, limit, offset)

    async def create(
        self, *, root_cause_link_id: UUID, root_cause_summary: str | None, started_at: datetime
    ) -> Incident:
        incident = Incident(
            root_cause_link_id=root_cause_link_id,
            root_cause_summary=root_cause_summary,
            status=IncidentStatus.OPEN,
            started_at=started_at,
        )
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def set_eta(self, incident: Incident, eta_at: datetime) -> Incident:
        incident.eta_at = eta_at
        await self.db.flush()
        return incident

    async def resolve(self, incident: Incident, resolved_at: datetime) -> Incident:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = resolved_at
        await self.db.flush()
        return incident

    async def list_affected_sites(self, incident_id: UUID) -> list[IncidentAffectedSite]:
        stmt = select(IncidentAffectedSite).where(IncidentAffectedSite.incident_id == incident_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_affected_site_if_missing(self, incident_id: UUID, site_id: UUID) -> None:
        stmt = select(IncidentAffectedSite).where(
            IncidentAffectedSite.incident_id == incident_id,
            IncidentAffectedSite.site_id == site_id,
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing is None:
            self.db.add(IncidentAffectedSite(incident_id=incident_id, site_id=site_id))
            await self.db.flush()

    async def add_timeline_event(
        self, incident_id: UUID, ts: datetime, label: str, detail: str
    ) -> IncidentTimelineEvent:
        event = IncidentTimelineEvent(incident_id=incident_id, ts=ts, label=label, detail=detail)
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_timeline(self, incident_id: UUID) -> list[IncidentTimelineEvent]:
        stmt = (
            select(IncidentTimelineEvent)
            .where(IncidentTimelineEvent.incident_id == incident_id)
            .order_by(IncidentTimelineEvent.ts)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
