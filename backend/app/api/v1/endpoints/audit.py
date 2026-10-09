from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import pagination_params, require_role
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditEventOut
from app.schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[
        Depends(require_role(UserRole.ADMIN)),
        Depends(rate_limit("admin", "rate_limit_admin_per_minute")),
    ],
)


@router.get("", response_model=PaginatedResponse[AuditEventOut])
async def list_audit_events(
    agent: str | None = None,
    actor_role: UserRole | None = None,
    entity: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditEventOut]:
    items, total = await AuditRepository(db).list_paginated(
        pagination.limit,
        pagination.offset,
        agent=agent,
        actor_role=actor_role,
        entity=entity,
        since=since,
        until=until,
    )
    return PaginatedResponse.build(items, total, pagination)
