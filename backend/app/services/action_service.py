from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.action import Action
from app.models.enums import ActionAgent, ActionStatus, AutonomyLevel, RiskLevel, UserRole
from app.models.user import User
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.settings_repository import SettingsRepository


class ActionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.actions = ActionRepository(db)
        self.audit = AuditRepository(db)
        self.settings = SettingsRepository(db)

    async def create_from_agent(
        self,
        *,
        incident_id: UUID,
        agent: ActionAgent,
        proposal: str,
        owner_role: UserRole,
        risk_level: RiskLevel,
        sources: list[dict],
    ) -> Action:
        """Autonomy level decides whether this waits in the queue or auto-executes.

        Only auto_low_risk + a LOW risk_level skips human approval; everything
        else is proposed and must be approved/rejected through the normal flow.
        """
        settings = await self.settings.get_singleton()
        auto_execute = (
            settings.autonomy_level == AutonomyLevel.AUTO_LOW_RISK and risk_level == RiskLevel.LOW
        )

        action = await self.actions.create(
            incident_id=incident_id,
            agent=agent,
            proposal=proposal,
            owner_role=owner_role,
            risk_level=risk_level,
            sources=sources,
            status=ActionStatus.EXECUTED if auto_execute else ActionStatus.PROPOSED,
            approved_at=datetime.now(UTC) if auto_execute else None,
        )

        if auto_execute:
            await self.audit.log(
                event_type="action.auto_executed",
                entity="action",
                entity_id=action.id,
                details={
                    "incident_id": str(incident_id),
                    "agent": agent.value,
                    "autonomy_level": settings.autonomy_level.value,
                },
            )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def list_actions(
        self,
        limit: int,
        offset: int,
        actor: User,
        *,
        status: ActionStatus | None = None,
        incident_id: UUID | None = None,
    ) -> tuple[list[Action], int]:
        owner_role = None if actor.role == UserRole.ADMIN else actor.role
        return await self.actions.list_paginated(
            limit, offset, owner_role=owner_role, status=status, incident_id=incident_id
        )

    async def _transition(
        self, action_id: UUID, target_status: ActionStatus, actor: User
    ) -> Action:
        action = await self.actions.get_by_id(action_id)
        if action is None:
            raise NotFoundError(f"Action {action_id} not found")

        if actor.role != UserRole.ADMIN and actor.role != action.owner_role:
            raise ForbiddenError(
                f"Role '{actor.role.value}' cannot act on an action owned by "
                f"'{action.owner_role.value}'"
            )

        if action.status == target_status:
            return action  # idempotent no-op
        if action.status != ActionStatus.PROPOSED:
            raise ConflictError(
                f"Action {action_id} is already '{action.status.value}' and cannot become "
                f"'{target_status.value}'"
            )

        action.status = target_status
        action.approved_by_user_id = actor.id
        action.approved_at = datetime.now(UTC)
        await self.db.flush()

        await self.audit.log(
            event_type=f"action.{target_status.value}",
            entity="action",
            entity_id=action.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
            details={"incident_id": str(action.incident_id), "agent": action.agent.value},
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def approve(self, action_id: UUID, actor: User) -> Action:
        return await self._transition(action_id, ActionStatus.APPROVED, actor)

    async def reject(self, action_id: UUID, actor: User) -> Action:
        return await self._transition(action_id, ActionStatus.REJECTED, actor)
