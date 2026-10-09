from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params, require_role
from app.db.session import get_db
from app.models.enums import IncidentStatus, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.incident import IncidentOut, IncidentTimelineEventOut, UpdateEtaIn
from app.services.incident_service import IncidentService

router = APIRouter(
    prefix="/incidents", tags=["incidents"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=PaginatedResponse[IncidentOut])
async def list_incidents(
    status: IncidentStatus | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[IncidentOut]:
    service = IncidentService(db)
    items, total = await service.list_incidents(pagination.limit, pagination.offset, status=status)
    return PaginatedResponse.build(items, total, pagination)


@router.get("/current", response_model=IncidentOut)
async def get_current_incident(db: AsyncSession = Depends(get_db)) -> IncidentOut:
    return await IncidentService(db).get_current_active()


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)) -> IncidentOut:
    return await IncidentService(db).get_incident(incident_id)


@router.get("/{incident_id}/timeline", response_model=list[IncidentTimelineEventOut])
async def get_incident_timeline(
    incident_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[IncidentTimelineEventOut]:
    return await IncidentService(db).get_timeline(incident_id)


@router.put(
    "/{incident_id}/eta",
    response_model=IncidentOut,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER))],
)
async def update_incident_eta(
    incident_id: UUID,
    payload: UpdateEtaIn,
    actor: User = Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER)),
    db: AsyncSession = Depends(get_db),
) -> IncidentOut:
    return await IncidentService(db).update_eta(incident_id, payload.eta_at, actor)


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentOut,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER))],
)
async def resolve_incident(
    incident_id: UUID,
    actor: User = Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER)),
    db: AsyncSession = Depends(get_db),
) -> IncidentOut:
    return await IncidentService(db).resolve(incident_id, actor)
