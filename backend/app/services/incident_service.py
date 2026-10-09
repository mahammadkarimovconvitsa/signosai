from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import IncidentStatus, OperationalStatus
from app.models.incident import Incident
from app.models.user import User
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.network_repository import LinkRepository, SiteRepository
from app.schemas.incident import IncidentOut, IncidentTimelineEventOut
from app.schemas.network import SiteOut


class IncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.incidents = IncidentRepository(db)
        self.alarms = AlarmRepository(db)
        self.sites = SiteRepository(db)
        self.links = LinkRepository(db)
        self.audit = AuditRepository(db)

    async def _to_out(self, incident: Incident) -> IncidentOut:
        affected = await self.incidents.list_affected_sites(incident.id)
        sites = await self.sites.get_many([a.site_id for a in affected])
        alarms = await self.alarms.list_for_incident(incident.id)
        return IncidentOut(
            id=incident.id,
            root_cause_link_id=incident.root_cause_link_id,
            root_cause_summary=incident.root_cause_summary,
            status=incident.status,
            started_at=incident.started_at,
            eta_at=incident.eta_at,
            resolved_at=incident.resolved_at,
            alarm_count=len(alarms),
            affected_sites=[SiteOut.model_validate(s) for s in sites],
        )

    async def get_incident(self, incident_id: UUID) -> IncidentOut:
        incident = await self.incidents.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError(f"Incident {incident_id} not found")
        return await self._to_out(incident)

    async def get_current_active(self) -> IncidentOut:
        incident = await self.incidents.get_current_active()
        if incident is None:
            raise NotFoundError("No active incident")
        return await self._to_out(incident)

    async def list_incidents(
        self, limit: int, offset: int, *, status: IncidentStatus | None = None
    ) -> tuple[list[IncidentOut], int]:
        incidents, total = await self.incidents.list_paginated(limit, offset, status=status)
        return [await self._to_out(i) for i in incidents], total

    async def get_timeline(self, incident_id: UUID) -> list[IncidentTimelineEventOut]:
        await self.get_incident(incident_id)  # 404 if missing
        events = await self.incidents.list_timeline(incident_id)
        return [IncidentTimelineEventOut.model_validate(e) for e in events]

    async def update_eta(self, incident_id: UUID, eta_at: datetime, actor: User) -> IncidentOut:
        incident = await self.incidents.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError(f"Incident {incident_id} not found")
        incident = await self.incidents.set_eta(incident, eta_at)
        await self.incidents.add_timeline_event(
            incident.id, datetime.now(UTC), "eta_updated", f"ETA set to {eta_at.isoformat()}"
        )
        await self.audit.log(
            event_type="incident.eta_updated",
            entity="incident",
            entity_id=incident.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
            details={"eta_at": eta_at.isoformat()},
        )
        await self.db.commit()
        return await self._to_out(incident)

    async def resolve(self, incident_id: UUID, actor: User) -> IncidentOut:
        incident = await self.incidents.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError(f"Incident {incident_id} not found")
        if incident.status == IncidentStatus.RESOLVED:
            return await self._to_out(incident)

        now = datetime.now(UTC)
        affected = await self.incidents.list_affected_sites(incident.id)
        sites = await self.sites.get_many([a.site_id for a in affected])
        for site in sites:
            await self.sites.set_status(site, OperationalStatus.UP)

        link = await self.links.get_by_id(incident.root_cause_link_id)
        if link is not None:
            await self.links.set_status(link, OperationalStatus.UP)

        incident = await self.incidents.resolve(incident, now)
        await self.incidents.add_timeline_event(incident.id, now, "resolved", "Incident resolved")
        await self.audit.log(
            event_type="incident.resolved",
            entity="incident",
            entity_id=incident.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
        )
        await self.db.commit()
        return await self._to_out(incident)
