from sqlalchemy import select

from app.models.market_item import MarketItem
from app.repositories.base import BaseRepository


class MarketRepository(BaseRepository):
    async def list_paginated(self, limit: int, offset: int) -> tuple[list[MarketItem], int]:
        stmt = select(MarketItem).order_by(MarketItem.published_at.desc())
        return await self.paginate(stmt, limit, offset)
