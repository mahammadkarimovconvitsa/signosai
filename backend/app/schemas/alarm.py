from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlarmSeverity


class AlarmIn(BaseModel):
    timestamp: datetime
    site_id: UUID
    cell_id: UUID | None = None
    link_id: UUID | None = None
    severity: AlarmSeverity
    type: str


class AlarmBatchIn(BaseModel):
    alarms: list[AlarmIn]


class AlarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    site_id: UUID
    cell_id: UUID | None
    link_id: UUID | None
    severity: AlarmSeverity
    type: str
    processed: bool
    incident_id: UUID | None


class AlarmIngestResult(BaseModel):
    ingested: int
    incident_id: UUID | None
