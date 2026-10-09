from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.metric import Metric
from app.services.explain_service import ExplainService

router = APIRouter(prefix="/explain", tags=["explain"], dependencies=[Depends(get_current_user)])


@router.get("/{metric_id}", response_model=Metric)
async def explain_metric(metric_id: str, db: AsyncSession = Depends(get_db)) -> Metric:
    return await ExplainService(db).explain(metric_id)
