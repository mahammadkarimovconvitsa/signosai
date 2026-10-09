import asyncio
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.services.incident_service import IncidentService

router = APIRouter(tags=["stream"], dependencies=[Depends(get_current_user)])


async def _incident_event_stream(
    incident_id: UUID, request: Request, db: AsyncSession
) -> AsyncGenerator[str, None]:
    settings = get_settings()
    last_payload: str | None = None
    while True:
        if await request.is_disconnected():
            break

        # One session for the whole connection (its lifetime is tied to this
        # request's Depends(get_db), which FastAPI keeps open until the
        # StreamingResponse finishes) -- expire_all() forces each poll to
        # re-read from the DB instead of returning identity-mapped objects
        # from the first fetch.
        db.expire_all()
        try:
            incident = await IncidentService(db).get_incident(incident_id)
        except NotFoundError:
            yield 'event: error\ndata: {"message": "incident not found"}\n\n'
            return

        payload = incident.model_dump_json()
        if payload != last_payload:
            yield f"event: incident\ndata: {payload}\n\n"
            last_payload = payload
        else:
            yield ": keep-alive\n\n"

        await asyncio.sleep(settings.sse_poll_seconds)


@router.get("/incidents/{incident_id}/stream")
async def stream_incident(
    incident_id: UUID, request: Request, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    return StreamingResponse(
        _incident_event_stream(incident_id, request, db), media_type="text/event-stream"
    )
