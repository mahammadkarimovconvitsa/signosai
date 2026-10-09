from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditRepository(db)

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        items, total = await self.users.list_paginated(limit, offset)
        await self.db.commit()
        return items, total

    async def create_user(self, payload: UserCreate, actor: User) -> User:
        if await self.users.get_by_email(payload.email) is not None:
            raise ConflictError(f"A user with email '{payload.email}' already exists")
        user = await self.users.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        await self.audit.log(
            event_type="user.created",
            entity="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
            details={"email": user.email, "role": user.role.value},
        )
        await self.db.commit()
        return user

    async def set_active(self, user_id: UUID, is_active: bool, actor: User) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        user = await self.users.set_active(user, is_active)
        await self.audit.log(
            event_type="user.deactivated" if not is_active else "user.activated",
            entity="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
        )
        await self.db.commit()
        return user
