from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ActionAgent, ActionStatus, RiskLevel, UserRole


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    agent: ActionAgent
    proposal: str
    owner_role: UserRole
    status: ActionStatus
    risk_level: RiskLevel
    sources: list[dict]
    approved_by_user_id: UUID | None
    approved_at: datetime | None
