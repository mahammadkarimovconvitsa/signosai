import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def test_create_user_requires_admin(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "engineer@signos.app", UserRole.ENGINEER)
    resp = await client.post(
        "/api/v1/users",
        json={"email": "new@signos.app", "password": "secret123", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_create_and_list_users(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.post(
        "/api/v1/users",
        json={"email": "new@signos.app", "password": "secret123", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@signos.app"

    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2  # admin + new user


async def test_create_duplicate_user_conflicts(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    payload = {"email": "dup@signos.app", "password": "secret123", "role": "viewer"}
    resp = await client.post("/api/v1/users", json=payload, headers=headers)
    assert resp.status_code == 201
    resp = await client.post("/api/v1/users", json=payload, headers=headers)
    assert resp.status_code == 409


async def test_deactivate_and_reactivate_user(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "admin@signos.app", UserRole.ADMIN)
    resp = await client.post(
        "/api/v1/users",
        json={"email": "temp@signos.app", "password": "secret123", "role": "engineer"},
        headers=headers,
    )
    user_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/users/{user_id}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "temp@signos.app", "password": "secret123"}
    )
    assert login_resp.status_code == 401

    resp = await client.post(f"/api/v1/users/{user_id}/activate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True
