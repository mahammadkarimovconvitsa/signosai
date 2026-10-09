from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EnterpriseCustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sector: str
    account_manager_user_id: UUID | None
