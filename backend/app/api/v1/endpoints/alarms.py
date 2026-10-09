from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import pagination_params, require_role
from app.core.rate_limit import rate_limit
from app.db.session import AsyncSessionLocal, get_db
from app.models.enums import UserRole
from app.schemas.alarm import AlarmBatchIn, AlarmIngestResult, AlarmOut
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.agent_orchestration_service import AgentOrchestrationService
from app.services.alarm_service import AlarmService

router = APIRouter(prefix="/alarms", tags=["alarms"])


async def _run_agents_background(incident_id: UUID) -> None:
    # A fresh session, never the request-scoped one: this runs after the
    # response is sent, by which point the request's session may be closing.
    async with AsyncSessionLocal() as db:
        await AgentOrchestrationService(db).run_for_incident(incident_id)


@router.post(
    "/ingest",
    response_model=AlarmIngestResult,
    dependencies=[
        Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER)),
        Depends(rate_limit("ingestion", "rate_limit_ingestion_per_minute")),
    ],
)
async def ingest_alarms(
    payload: AlarmBatchIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> AlarmIngestResult:
    result = await AlarmService(db).ingest(payload.alarms)
    if result.incident_id is not None:
        background_tasks.add_task(_run_agents_background, result.incident_id)
    return result


@router.get(
    "",
    response_model=PaginatedResponse[AlarmOut],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER, UserRole.VIEWER))],
)
async def list_alarms(
    processed: bool | None = None,
    site_id: UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AlarmOut]:
    service = AlarmService(db)
    items, total = await service.list_alarms(
        pagination.limit, pagination.offset, processed=processed, site_id=site_id
    )
    return PaginatedResponse.build(items, total, pagination)
