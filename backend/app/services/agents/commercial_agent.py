from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_client import generate_structured
from app.models.enums import ActionAgent
from app.services.agents.base import AgentRunResult, run_agent_with_fallback
from app.services.commercial_service import CommercialService

SYSTEM_PROMPT = """You are the Commercial agent for Signos, a telecom operations platform.
You draft a short compensation SMS for premium subscribers affected by a network
incident, in both Azerbaijani and English.

Rules:
- Never invent numbers — only use the affected subscriber count and compensation
  amount given to you in the input.
- Keep each SMS under 320 characters, apologetic but brief, and state the
  compensation amount in AZN.
- Do not include a phone number or link; this is a draft for a human to review.
"""


class CommercialAgentOutput(BaseModel):
    sms_az: str
    sms_en: str


async def _call(incident_id: UUID, db: AsyncSession):
    commercial = CommercialService(db)
    premium_count = await commercial.get_affected_premium_count(incident_id)
    compensation = await commercial.get_compensation_cost(incident_id)
    per_subscriber = compensation.value / premium_count.value if premium_count.value else 0

    user_prompt = (
        f"Incident id: {incident_id}\n"
        f"Affected premium subscribers: {premium_count.value}\n"
        f"Compensation per subscriber: {per_subscriber:.2f} AZN\n"
        f"Total compensation cost: {compensation.value:.2f} AZN\n"
    )

    return await generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=CommercialAgentOutput,
    )


async def run(db: AsyncSession, incident_id: UUID) -> AgentRunResult:
    return await run_agent_with_fallback(
        db, incident_id, ActionAgent.COMMERCIAL, lambda: _call(incident_id, db)
    )
