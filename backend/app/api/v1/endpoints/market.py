from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.market import MarketItemOut
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedResponse[MarketItemOut])
async def list_market_items(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[MarketItemOut]:
    items, total = await MarketService(db).list_items(pagination.limit, pagination.offset)
    return PaginatedResponse.build(items, total, pagination)
