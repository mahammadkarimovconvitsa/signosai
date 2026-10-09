from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import SubscriberSegment
from app.schemas.metric import Metric


class SubscriberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    home_cell_id: UUID
    segment: SubscriberSegment
    msisdn_masked: str
    name: str | None


class CommercialSummaryOut(BaseModel):
    incident_id: UUID
    affected_premium_subscribers: Metric
    compensation_cost_azn: Metric
    sample_subscribers: list[SubscriberOut]
