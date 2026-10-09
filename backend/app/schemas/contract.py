from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ContractType


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    type: ContractType
    restore_within_min: int
    penalty_per_started_hour_azn: float
    penalty_cap_azn: float
    clause_text: str
    valid_from: date
    valid_to: date | None
