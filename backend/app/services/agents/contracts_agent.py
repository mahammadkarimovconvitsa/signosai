from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_client import generate_structured
from app.models.enums import ActionAgent
from app.services.agents.base import AgentRunResult, run_agent_with_fallback
from app.services.impact_service import ImpactService
from app.services.sla_service import SlaService

SYSTEM_PROMPT = """You are the Contracts agent for Signos, a telecom operations platform.
You turn contract clause text into plain language for an account manager, and list
the obligations put at risk by the current incident.

Rules:
- Never invent numbers (penalties, deadlines, amounts) — only restate numbers
  given to you in the input, you do not compute anything yourself.
- Reference the contract id(s) given to you.
- Keep `summary` to 2-4 sentences in plain English, no legal jargon.
- `obligations` is a short list of concrete obligations at risk.
"""


class ContractsAgentOutput(BaseModel):
    summary: str
    obligations: list[str]


async def _call(incident_id: UUID, db: AsyncSession):
    impact = ImpactService(db)
    sla = SlaService(db)

    contracts = await impact.get_affected_contracts(incident_id)
    if not contracts:
        contracts_block = "No contracts affected."
    else:
        lines = []
        for contract in contracts:
            contract_sla = await sla.get_contract_sla(incident_id, contract)
            lines.append(
                f"- contract {contract.id} (type={contract.type.value}): "
                f"clause: \"{contract.clause_text}\"; "
                f"compliance={contract_sla.compliance_status.value}; "
                f"time_remaining_min={contract_sla.time_remaining_min.value:.1f}; "
                f"worst_case_penalty_azn={contract_sla.worst_case_penalty_azn.value}"
            )
        contracts_block = "\n".join(lines)

    user_prompt = f"Incident id: {incident_id}\nAffected contracts:\n{contracts_block}\n"

    return await generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=ContractsAgentOutput,
    )


async def run(db: AsyncSession, incident_id: UUID) -> AgentRunResult:
    return await run_agent_with_fallback(
        db, incident_id, ActionAgent.CONTRACTS, lambda: _call(incident_id, db)
    )
