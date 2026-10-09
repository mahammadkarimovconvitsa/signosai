from uuid import UUID

from sqlalchemy import select

from app.models.agent_output import AgentOutput
from app.models.enums import ActionAgent
from app.repositories.base import BaseRepository


class AgentOutputRepository(BaseRepository):
    async def create(
        self,
        *,
        incident_id: UUID,
        agent: ActionAgent,
        output: dict,
        source: str,
        model: str,
        tokens: int | None,
        latency_ms: int | None,
    ) -> AgentOutput:
        row = AgentOutput(
            incident_id=incident_id,
            agent=agent,
            output=output,
            source=source,
            model=model,
            tokens=tokens,
            latency_ms=latency_ms,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def get_latest(self, incident_id: UUID, agent: ActionAgent) -> AgentOutput | None:
        stmt = (
            select(AgentOutput)
            .where(AgentOutput.incident_id == incident_id, AgentOutput.agent == agent)
            .order_by(AgentOutput.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_incident(self, incident_id: UUID) -> list[AgentOutput]:
        stmt = select(AgentOutput).where(AgentOutput.incident_id == incident_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
