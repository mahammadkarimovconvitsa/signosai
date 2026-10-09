from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.network import CellOut, LinkOut, SiteOut
from app.services.network_service import NetworkService

router = APIRouter(prefix="/network", tags=["network"], dependencies=[Depends(get_current_user)])


@router.get("/sites", response_model=PaginatedResponse[SiteOut])
async def list_sites(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SiteOut]:
    items, total = await NetworkService(db).list_sites(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)


@router.get("/sites/{site_id}", response_model=SiteOut)
async def get_site(site_id: UUID, db: AsyncSession = Depends(get_db)) -> SiteOut:
    return await NetworkService(db).get_site(site_id)


@router.get("/links", response_model=PaginatedResponse[LinkOut])
async def list_links(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LinkOut]:
    items, total = await NetworkService(db).list_links(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)


@router.get("/cells", response_model=PaginatedResponse[CellOut])
async def list_cells(
    site_id: UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CellOut]:
    service = NetworkService(db)
    items, total = await service.list_cells(pagination.limit, pagination.offset, site_id)
    return PaginatedResponse.build(items, total, pagination)
