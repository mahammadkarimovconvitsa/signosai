from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import pagination_params, require_role
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[
        Depends(require_role(UserRole.ADMIN)),
        Depends(rate_limit("admin", "rate_limit_admin_per_minute")),
    ],
)


@router.get("", response_model=PaginatedResponse[UserOut])
async def list_users(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserOut]:
    items, total = await UserService(db).list_users(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    return await UserService(db).create_user(payload, actor)


@router.post("/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(
    user_id: UUID,
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    return await UserService(db).set_active(user_id, False, actor)


@router.post("/{user_id}/activate", response_model=UserOut)
async def activate_user(
    user_id: UUID,
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    return await UserService(db).set_active(user_id, True, actor)
