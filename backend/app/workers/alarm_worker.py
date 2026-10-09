import asyncio
import contextlib
import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.agent_orchestration_service import AgentOrchestrationService
from app.services.correlation_service import CorrelationService

logger = logging.getLogger(__name__)


async def run_alarm_worker(stop_event: asyncio.Event) -> None:
    """Polls for alarms written directly to the DB (outside the ingestion API)
    and correlates them, so the data engineer can push alarms either way."""
    settings = get_settings()
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                incident = await CorrelationService(db).correlate()
                if incident is not None:
                    logger.info("alarm_worker: correlated into incident %s", incident.id)
                    await AgentOrchestrationService(db).run_for_incident(incident.id)
        except Exception:
            logger.exception("alarm_worker: correlation pass failed")

        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=settings.alarm_worker_poll_seconds)
