from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models.action import Action
from app.models.enums import ActionAgent, ActionStatus, RiskLevel, UserRole
from app.repositories.base import BaseRepository


class ActionRepository(BaseRepository):
    async def get_by_id(self, action_id: UUID) -> Action | None:
        return await self.db.get(Action, action_id)

    async def create(
        self,
        *,
        incident_id: UUID,
        agent: ActionAgent,
        proposal: str,
        owner_role: UserRole,
        risk_level: RiskLevel,
        sources: list[dict],
        status: ActionStatus = ActionStatus.PROPOSED,
        approved_at: datetime | None = None,
    ) -> Action:
        action = Action(
            incident_id=incident_id,
            agent=agent,
            proposal=proposal,
            owner_role=owner_role,
            risk_level=risk_level,
            sources=sources,
            status=status,
            approved_at=approved_at,
        )
        self.db.add(action)
        await self.db.flush()
        await self.db.refresh(action)
        return action

    async def list_paginated(
        self,
        limit: int,
        offset: int,
        *,
        owner_role: UserRole | None = None,
        status: ActionStatus | None = None,
        incident_id: UUID | None = None,
    ) -> tuple[list[Action], int]:
        stmt = select(Action).order_by(Action.created_at.desc())
        if owner_role is not None:
            stmt = stmt.where(Action.owner_role == owner_role)
        if status is not None:
            stmt = stmt.where(Action.status == status)
        if incident_id is not None:
            stmt = stmt.where(Action.incident_id == incident_id)
        return await self.paginate(stmt, limit, offset)
