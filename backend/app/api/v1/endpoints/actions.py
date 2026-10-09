from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params
from app.db.session import get_db
from app.models.enums import ActionStatus
from app.models.user import User
from app.schemas.action import ActionOut
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["actions"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedResponse[ActionOut])
async def list_actions(
    status: ActionStatus | None = None,
    incident_id: UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ActionOut]:
    service = ActionService(db)
    items, total = await service.list_actions(
        pagination.limit, pagination.offset, actor, status=status, incident_id=incident_id
    )
    return PaginatedResponse.build(items, total, pagination)


@router.post("/{action_id}/approve", response_model=ActionOut)
async def approve_action(
    action_id: UUID,
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActionOut:
    return await ActionService(db).approve(action_id, actor)


@router.post("/{action_id}/reject", response_model=ActionOut)
async def reject_action(
    action_id: UUID,
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActionOut:
    return await ActionService(db).reject(action_id, actor)
