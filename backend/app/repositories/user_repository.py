from uuid import UUID

from sqlalchemy import select

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def any_admin_exists(self) -> bool:
        result = await self.db.execute(select(User.id).where(User.role == UserRole.ADMIN).limit(1))
        return result.scalar_one_or_none() is not None

    async def create(self, *, email: str, hashed_password: str, role: UserRole) -> User:
        user = User(email=email, hashed_password=hashed_password, role=role)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_paginated(self, limit: int, offset: int) -> tuple[list[User], int]:
        return await self.paginate(select(User).order_by(User.email), limit, offset)

    async def set_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        await self.db.flush()
        await self.db.refresh(user)
        return user
