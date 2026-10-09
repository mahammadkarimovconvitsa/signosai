from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    actor_user_id: UUID | None
    actor_role: UserRole | None
    event_type: str
    entity: str
    entity_id: UUID | None
    details: dict
