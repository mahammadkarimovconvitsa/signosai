from collections import Counter
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_client import generate_structured
from app.models.enums import ActionAgent
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.runbook_repository import RunbookRepository
from app.services.agents.base import AgentRunResult, run_agent_with_fallback

SYSTEM_PROMPT = """You are the Network agent for Signos, a telecom operations platform.
You explain network incidents to engineers. You are given a root cause, a list of
alarm ids, and relevant runbook steps if any exist.

Rules:
- Never invent numbers (alarm counts, site counts, durations) — only use numbers
  given to you in the input.
- Your `root_cause` and `summary` must reference the alarm ids given to you.
- If runbook steps were provided, base your `runbook` output on them; otherwise
  propose generic, safe first steps for the given failure type.
- Keep `summary` to 2-3 sentences. `runbook` is a short numbered list of steps.
"""


class NetworkAgentOutput(BaseModel):
    summary: str
    root_cause: str
    runbook: list[str]


async def _call(incident_id: UUID, db: AsyncSession):
    incidents = IncidentRepository(db)
    alarms = AlarmRepository(db)
    runbooks = RunbookRepository(db)

    incident = await incidents.get_by_id(incident_id)
    incident_alarms = await alarms.list_for_incident(incident_id)
    alarm_ids = [str(a.id) for a in incident_alarms]
    dominant_type = Counter(a.type for a in incident_alarms).most_common(1)
    failure_type = dominant_type[0][0] if dominant_type else "unknown"
    matching_runbooks = await runbooks.list_for_failure_type(failure_type)

    user_prompt = (
        f"Incident id: {incident_id}\n"
        f"Root cause (from deterministic correlation): {incident.root_cause_summary}\n"
        f"Failure type: {failure_type}\n"
        f"Alarm ids ({len(alarm_ids)} total): {', '.join(alarm_ids)}\n"
        f"Runbook steps on file for this failure type: "
        f"{[rb.steps for rb in matching_runbooks] or 'none on file'}\n"
    )

    return await generate_structured(
        system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, response_schema=NetworkAgentOutput
    )


async def run(db: AsyncSession, incident_id: UUID) -> AgentRunResult:
    return await run_agent_with_fallback(
        db, incident_id, ActionAgent.NETWORK, lambda: _call(incident_id, db)
    )
