from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import IncidentStatus
from app.schemas.network import SiteOut


class IncidentOut(BaseModel):
    id: UUID
    root_cause_link_id: UUID
    root_cause_summary: str | None
    status: IncidentStatus
    started_at: datetime
    eta_at: datetime | None
    resolved_at: datetime | None
    alarm_count: int
    affected_sites: list[SiteOut]


class IncidentTimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ts: datetime
    label: str
    detail: str


class UpdateEtaIn(BaseModel):
    eta_at: datetime
