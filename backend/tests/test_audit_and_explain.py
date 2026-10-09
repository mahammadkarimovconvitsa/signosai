import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def test_audit_requires_admin(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.get("/api/v1/audit", headers=headers)
    assert resp.status_code == 403


async def test_audit_captures_settings_update(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    await client.put(
        "/api/v1/settings", json={"autonomy_level": "approve_to_act"}, headers=headers
    )
    resp = await client.get("/api/v1/audit", headers=headers, params={"entity": "settings"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["items"][0]["event_type"] == "settings.updated"


async def test_explain_malformed_id_is_400(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get("/api/v1/explain/not-a-valid-id", headers=headers)
    assert resp.status_code == 422


async def test_explain_unknown_kind_is_404(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        "/api/v1/explain/nonexistent.thing:00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_explain_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/explain/finance.total_exposure:x")
    assert resp.status_code == 401
