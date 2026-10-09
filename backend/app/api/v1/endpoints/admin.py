from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[
        Depends(require_role(UserRole.ADMIN)),
        Depends(rate_limit("admin", "rate_limit_admin_per_minute")),
    ],
)


@router.post("/reset", status_code=204)
async def reset_operational_state(
    actor: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await AdminService(db).reset(actor)
