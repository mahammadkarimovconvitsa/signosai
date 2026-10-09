import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.gemini_client import GeminiCallResult
from app.models.enums import ActionAgent, AgentOutputSource
from app.repositories.agent_output_repository import AgentOutputRepository

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = [0.5, 1.5]


class AgentRunResult(BaseModel):
    agent: ActionAgent
    output: dict | None
    source: AgentOutputSource | None
    model: str | None
    latency_ms: int | None
    available: bool


async def run_agent_with_fallback(
    db: AsyncSession,
    incident_id: UUID,
    agent: ActionAgent,
    call_fn: Callable[[], Awaitable[GeminiCallResult]],
) -> AgentRunResult:
    """One retry/fallback policy shared by every agent.

    Tries the live call up to MAX_ATTEMPTS times (each bounded by
    agent_timeout_seconds), then falls back to this incident's most recent
    stored output for this agent. If neither exists, returns available=False
    — callers must never synthesize text to paper over that.
    """
    settings = get_settings()
    outputs = AgentOutputRepository(db)
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(call_fn(), timeout=settings.agent_timeout_seconds)
            latency_ms = int((time.monotonic() - start) * 1000)
            await outputs.create(
                incident_id=incident_id,
                agent=agent,
                output=result.data,
                source=AgentOutputSource.LIVE,
                model=result.model,
                tokens=result.tokens,
                latency_ms=latency_ms,
            )
            await db.commit()
            return AgentRunResult(
                agent=agent,
                output=result.data,
                source=AgentOutputSource.LIVE,
                model=result.model,
                latency_ms=latency_ms,
                available=True,
            )
        except Exception as exc:  # noqa: BLE001 - any failure falls back, not just API errors
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(BACKOFF_SECONDS[attempt])

    logger.warning("agent %s failed after %d attempts: %s", agent.value, MAX_ATTEMPTS, last_error)

    fallback = await outputs.get_latest(incident_id, agent)
    if fallback is not None:
        return AgentRunResult(
            agent=agent,
            output=fallback.output,
            source=AgentOutputSource.FALLBACK,
            model=fallback.model,
            latency_ms=None,
            available=True,
        )

    return AgentRunResult(
        agent=agent, output=None, source=None, model=None, latency_ms=None, available=False
    )
