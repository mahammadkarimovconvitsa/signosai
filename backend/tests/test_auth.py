import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _create_user(db_session: AsyncSession, role: UserRole = UserRole.ENGINEER) -> User:
    user = User(email="engineer@signos.app", hashed_password=hash_password("secret123"), role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    await _create_user(db_session)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "engineer@signos.app", "password": "secret123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    await _create_user(db_session)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "engineer@signos.app", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_me_requires_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_token(client: AsyncClient, db_session: AsyncSession):
    await _create_user(db_session)
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "engineer@signos.app", "password": "secret123"}
    )
    token = login_resp.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "engineer@signos.app"


async def test_refresh_flow(client: AsyncClient, db_session: AsyncSession):
    await _create_user(db_session)
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "engineer@signos.app", "password": "secret123"}
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_rejects_access_token(client: AsyncClient, db_session: AsyncSession):
    await _create_user(db_session)
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "engineer@signos.app", "password": "secret123"}
    )
    access_token = login_resp.json()["access_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
