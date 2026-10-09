from sqlalchemy import select

from app.models.runbook import Runbook
from app.repositories.base import BaseRepository


class RunbookRepository(BaseRepository):
    async def list_for_failure_type(self, failure_type: str) -> list[Runbook]:
        stmt = select(Runbook).where(Runbook.failure_type == failure_type)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
