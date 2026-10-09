from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import IncidentStatus, LinkType, OperationalStatus
from app.models.incident import Incident
from app.models.link import Link
from app.models.site import Site

pytestmark = pytest.mark.asyncio


async def test_login_rate_limit_returns_429_after_limit(
    client: AsyncClient, db_session: AsyncSession
):
    settings = get_settings()
    limit = settings.rate_limit_auth_per_minute

    for _ in range(limit):
        resp = await client.post(
            "/api/v1/auth/login", json={"email": "nobody@signos.app", "password": "wrong"}
        )
        assert resp.status_code == 401  # wrong creds, but not rate-limited yet

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@signos.app", "password": "wrong"}
    )
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limit_exceeded"


async def test_stream_requires_auth(client: AsyncClient):
    resp = await client.get(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/stream"
    )
    assert resp.status_code == 401


class _FakeRequest:
    """Standing in for the real Request: never reports disconnected, so the
    generator runs exactly as many loop iterations as we pull from it."""

    async def is_disconnected(self) -> bool:
        return False


async def test_stream_emits_incident_event(db_session: AsyncSession):
    # Exercises the generator directly rather than through full HTTP
    # streaming: under ASGITransport, the app and the test share one event
    # loop, and there's no guarantee the client ending the stream early
    # promptly delivers a disconnect to the server-side generator -- so a
    # real HTTP streaming test here risks leaking a never-ending background
    # task. The endpoint itself is a thin wrapper with nothing left to test
    # once this generator is covered.
    from app.api.v1.endpoints.stream import _incident_event_stream

    site = Site(
        name="S", lat=40.4, lng=49.8, district="Nasimi",
        energy_cost_azn_month=500, status=OperationalStatus.DOWN,
    )
    db_session.add(site)
    await db_session.flush()
    link = Link(
        from_site_id=site.id, to_site_id=site.id, type=LinkType.FIBER,
        is_protected=False, status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.flush()
    incident = Incident(
        root_cause_link_id=link.id, root_cause_summary="Fiber cut",
        status=IncidentStatus.OPEN, started_at=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    agen = _incident_event_stream(incident.id, _FakeRequest(), db_session)
    try:
        first_chunk = await agen.__anext__()
    finally:
        await agen.aclose()

    assert first_chunk.startswith("event: incident")
    assert str(incident.id) in first_chunk


async def test_stream_unknown_incident_emits_error_and_closes(db_session: AsyncSession):
    import uuid

    from app.api.v1.endpoints.stream import _incident_event_stream

    agen = _incident_event_stream(uuid.uuid4(), _FakeRequest(), db_session)
    chunks = [chunk async for chunk in agen]
    assert len(chunks) == 1
    assert chunks[0].startswith("event: error")
