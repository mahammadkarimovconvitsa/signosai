from uuid import UUID

from pydantic import BaseModel

from app.schemas.metric import Metric


class FinanceSummaryOut(BaseModel):
    incident_id: UUID
    revenue_per_min_azn: Metric
    lost_revenue_azn: Metric
    projected_penalties_azn: Metric
    compensation_cost_azn: Metric
    total_exposure_azn: Metric
