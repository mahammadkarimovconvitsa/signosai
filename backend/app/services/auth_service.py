from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import TokenType, create_token, decode_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return user

    def issue_tokens(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_token(user.id, user.role.value, TokenType.ACCESS),
            refresh_token=create_token(user.id, user.role.value, TokenType.REFRESH),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired refresh token") from exc

        if payload.get("type") != TokenType.REFRESH.value:
            raise UnauthorizedError("Token is not a refresh token")

        user = await self.users.get_by_id(UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User no longer active")

        return self.issue_tokens(user)

    async def ensure_first_admin(self, email: str, password: str) -> None:
        if await self.users.any_admin_exists():
            return
        existing = await self.users.get_by_email(email)
        if existing is not None:
            return
        await self.users.create(
            email=email, hashed_password=hash_password(password), role=UserRole.ADMIN
        )
        await self.db.commit()
