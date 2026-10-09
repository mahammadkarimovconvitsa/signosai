from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def paginate(self, stmt: Select, limit: int, offset: int) -> tuple[list, int]:
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()
        rows = await self.db.execute(stmt.limit(limit).offset(offset))
        return list(rows.scalars().all()), total
