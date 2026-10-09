from pydantic import BaseModel

from app.schemas.customer import EnterpriseCustomerOut
from app.schemas.sla import ContractSlaOut


class CustomerImpactOut(BaseModel):
    customer: EnterpriseCustomerOut
    contracts: list[ContractSlaOut]
