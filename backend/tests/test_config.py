import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def test_settings_requires_admin(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 403


async def test_settings_get_creates_singleton(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["autonomy_level"] == "recommend_only"


async def test_settings_update(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.put(
        "/api/v1/settings", json={"autonomy_level": "approve_to_act"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["autonomy_level"] == "approve_to_act"

    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.json()["autonomy_level"] == "approve_to_act"


async def test_business_config_crud(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)

    resp = await client.get("/api/v1/business-config/default_eta_min", headers=headers)
    assert resp.status_code == 404

    resp = await client.put(
        "/api/v1/business-config/default_eta_min",
        json={"value": "180", "description": "Default repair ETA in minutes"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "180"

    resp = await client.get("/api/v1/business-config", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
