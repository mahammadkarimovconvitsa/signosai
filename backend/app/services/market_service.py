from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_item import MarketItem
from app.repositories.market_repository import MarketRepository


class MarketService:
    def __init__(self, db: AsyncSession):
        self.market = MarketRepository(db)

    async def list_items(self, limit: int, offset: int) -> tuple[list[MarketItem], int]:
        return await self.market.list_paginated(limit, offset)
