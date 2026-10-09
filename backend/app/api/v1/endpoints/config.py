from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import pagination_params, require_role
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.config import BusinessConfigOut, BusinessConfigUpdate, SettingsOut, SettingsUpdate
from app.services.config_service import ConfigService

router = APIRouter(
    dependencies=[
        Depends(require_role(UserRole.ADMIN)),
        Depends(rate_limit("admin", "rate_limit_admin_per_minute")),
    ]
)


@router.get("/settings", response_model=SettingsOut, tags=["settings"])
async def get_settings(db: AsyncSession = Depends(get_db)) -> SettingsOut:
    return await ConfigService(db).get_settings()


@router.put("/settings", response_model=SettingsOut, tags=["settings"])
async def update_settings(
    payload: SettingsUpdate,
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SettingsOut:
    return await ConfigService(db).update_settings(payload.autonomy_level, actor)


@router.get(
    "/business-config",
    response_model=PaginatedResponse[BusinessConfigOut],
    tags=["business-config"],
)
async def list_business_config(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BusinessConfigOut]:
    service = ConfigService(db)
    items, total = await service.list_business_config(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)


@router.get(
    "/business-config/{key}", response_model=BusinessConfigOut, tags=["business-config"]
)
async def get_business_config(key: str, db: AsyncSession = Depends(get_db)) -> BusinessConfigOut:
    return await ConfigService(db).get_business_config(key)


@router.put(
    "/business-config/{key}", response_model=BusinessConfigOut, tags=["business-config"]
)
async def update_business_config(
    key: str,
    payload: BusinessConfigUpdate,
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BusinessConfigOut:
    return await ConfigService(db).update_business_config(
        key, payload.value, payload.description, actor
    )
