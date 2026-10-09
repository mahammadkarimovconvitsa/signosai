from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.contract import Contract
from app.repositories.contract_repository import ContractRepository


class ContractService:
    def __init__(self, db: AsyncSession):
        self.contracts = ContractRepository(db)

    async def list_contracts(
        self, limit: int, offset: int, customer_id: UUID | None = None
    ) -> tuple[list[Contract], int]:
        return await self.contracts.list_paginated(limit, offset, customer_id)

    async def get_contract(self, contract_id: UUID) -> Contract:
        contract = await self.contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError(f"Contract {contract_id} not found")
        return contract
