from uuid import UUID

from sqlalchemy import select

from app.models.contract import Contract
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository):
    async def list_paginated(
        self, limit: int, offset: int, customer_id: UUID | None = None
    ) -> tuple[list[Contract], int]:
        stmt = select(Contract).order_by(Contract.created_at)
        if customer_id is not None:
            stmt = stmt.where(Contract.customer_id == customer_id)
        return await self.paginate(stmt, limit, offset)

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        return await self.db.get(Contract, contract_id)

    async def list_by_customer_ids(self, customer_ids: list[UUID]) -> list[Contract]:
        if not customer_ids:
            return []
        result = await self.db.execute(
            select(Contract).where(Contract.customer_id.in_(customer_ids))
        )
        return list(result.scalars().all())
