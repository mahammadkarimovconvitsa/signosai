from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

DEFAULT_PASSWORD = "secret123"


async def create_user(
    db_session: AsyncSession, email: str, role: UserRole = UserRole.ENGINEER
) -> User:
    user = User(email=email, hashed_password=hash_password(DEFAULT_PASSWORD), role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def auth_headers(client, db_session: AsyncSession, email: str, role: UserRole) -> dict:
    await create_user(db_session, email, role)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": DEFAULT_PASSWORD}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
