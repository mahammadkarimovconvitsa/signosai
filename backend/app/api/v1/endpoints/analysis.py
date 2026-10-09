from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.commercial import CommercialSummaryOut
from app.schemas.finance import FinanceSummaryOut
from app.schemas.impact import CustomerImpactOut
from app.schemas.sla import ContractSlaOut
from app.services.commercial_service import CommercialService
from app.services.finance_service import FinanceService
from app.services.sla_service import SlaService

router = APIRouter(
    prefix="/incidents/{incident_id}", tags=["analysis"], dependencies=[Depends(get_current_user)]
)


@router.get("/impact", response_model=list[CustomerImpactOut])
async def get_incident_impact(
    incident_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[CustomerImpactOut]:
    return await SlaService(db).get_customer_impact(incident_id)


@router.get("/sla", response_model=list[ContractSlaOut])
async def get_incident_sla(
    incident_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[ContractSlaOut]:
    return await SlaService(db).get_incident_sla(incident_id)


@router.get("/finance", response_model=FinanceSummaryOut)
async def get_incident_finance(
    incident_id: UUID, db: AsyncSession = Depends(get_db)
) -> FinanceSummaryOut:
    return await FinanceService(db).get_summary(incident_id)


@router.get("/commercial", response_model=CommercialSummaryOut)
async def get_incident_commercial(
    incident_id: UUID, db: AsyncSession = Depends(get_db)
) -> CommercialSummaryOut:
    return await CommercialService(db).get_summary(incident_id)
