from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.enums import UserRole
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    async def log(
        self,
        *,
        event_type: str,
        entity: str,
        entity_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        actor_role: UserRole | None = None,
        details: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(UTC),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            event_type=event_type,
            entity=entity,
            entity_id=entity_id,
            details=details or {},
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_paginated(
        self,
        limit: int,
        offset: int,
        *,
        agent: str | None = None,
        actor_role: UserRole | None = None,
        entity: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> tuple[list[AuditEvent], int]:
        stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc())
        if entity is not None:
            stmt = stmt.where(AuditEvent.entity == entity)
        if actor_role is not None:
            stmt = stmt.where(AuditEvent.actor_role == actor_role)
        if agent is not None:
            stmt = stmt.where(AuditEvent.event_type.ilike(f"%{agent}%"))
        if since is not None:
            stmt = stmt.where(AuditEvent.timestamp >= since)
        if until is not None:
            stmt = stmt.where(AuditEvent.timestamp <= until)
        return await self.paginate(stmt, limit, offset)
