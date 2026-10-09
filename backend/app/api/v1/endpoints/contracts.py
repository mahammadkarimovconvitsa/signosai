from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, pagination_params
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.contract import ContractOut
from app.services.contract_service import ContractService

router = APIRouter(
    prefix="/contracts", tags=["contracts"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=PaginatedResponse[ContractOut])
async def list_contracts(
    customer_id: UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ContractOut]:
    items, total = await ContractService(db).list_contracts(
        pagination.limit, pagination.offset, customer_id
    )
    return PaginatedResponse.build(items, total, pagination)


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(contract_id: UUID, db: AsyncSession = Depends(get_db)) -> ContractOut:
    return await ContractService(db).get_contract(contract_id)
