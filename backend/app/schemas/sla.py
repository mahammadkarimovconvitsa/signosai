from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ComplianceStatus
from app.schemas.metric import Metric


class ContractSlaOut(BaseModel):
    contract_id: UUID
    customer_id: UUID
    deadline: Metric
    time_remaining_min: Metric
    compliance_status: ComplianceStatus
    penalty_accrued_so_far_azn: Metric
    projected_penalty_at_eta_azn: Metric | None
    worst_case_penalty_azn: Metric
