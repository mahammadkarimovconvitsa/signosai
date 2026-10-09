from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.portfolio import SitePortfolioOut
from app.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/portfolio", tags=["portfolio"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=PaginatedResponse[SitePortfolioOut])
async def list_portfolio(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SitePortfolioOut]:
    items, total = await PortfolioService(db).list_portfolio(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)
