import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActionAgent, RiskLevel, UserRole
from app.services.action_service import ActionService
from app.services.agents import commercial_agent, contracts_agent, network_agent
from app.services.agents.base import AgentRunResult
from app.services.commercial_service import CommercialService
from app.services.impact_service import ImpactService


class AgentOrchestrationService:
    """Runs all three agents for an incident and turns their output into
    proposed actions. Meant to be awaited from a background task so the
    triggering request (alarm ingestion) never blocks on the LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.actions = ActionService(db)
        self.impact = ImpactService(db)
        self.commercial = CommercialService(db)

    async def run_for_incident(self, incident_id: UUID) -> list[AgentRunResult]:
        results = await asyncio.gather(
            network_agent.run(self.db, incident_id),
            contracts_agent.run(self.db, incident_id),
            commercial_agent.run(self.db, incident_id),
        )

        for result in results:
            if result.available:
                await self.create_action_for_result(incident_id, result)

        return list(results)

    async def create_action_for_result(self, incident_id: UUID, result: AgentRunResult) -> None:
        if result.agent == ActionAgent.NETWORK:
            await self.actions.create_from_agent(
                incident_id=incident_id,
                agent=ActionAgent.NETWORK,
                proposal=result.output["summary"],
                owner_role=UserRole.ENGINEER,
                risk_level=RiskLevel.MEDIUM,
                sources=[{"table": "incidents", "id": str(incident_id)}],
            )
        elif result.agent == ActionAgent.CONTRACTS:
            contracts = await self.impact.get_affected_contracts(incident_id)
            await self.actions.create_from_agent(
                incident_id=incident_id,
                agent=ActionAgent.CONTRACTS,
                proposal=result.output["summary"],
                owner_role=UserRole.ACCOUNT_MANAGER,
                risk_level=RiskLevel.LOW,
                sources=[{"table": "contracts", "id": str(c.id)} for c in contracts],
            )
        elif result.agent == ActionAgent.COMMERCIAL:
            premium_count = await self.commercial.get_affected_premium_count(incident_id)
            await self.actions.create_from_agent(
                incident_id=incident_id,
                agent=ActionAgent.COMMERCIAL,
                proposal=result.output["sms_en"],
                owner_role=UserRole.ACCOUNT_MANAGER,
                risk_level=RiskLevel.LOW,
                sources=[s.model_dump() for s in premium_count.sources],
            )
