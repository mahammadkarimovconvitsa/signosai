from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.incident_repository import IncidentRepository
from app.schemas.finance import FinanceSummaryOut
from app.schemas.metric import Metric, SourceRef
from app.services.commercial_service import CommercialService
from app.services.impact_service import ImpactService
from app.services.sla_service import SlaService


class FinanceService:
    """Composes SLA + Commercial into one exposure figure.

    Revenue loss and projected penalties both use the same projection point —
    the incident's ETA once set, otherwise "now" — so every exposure component
    answers the same question: "what has this incident cost so far/by its ETA".
    """

    def __init__(self, db: AsyncSession):
        self.incidents = IncidentRepository(db)
        self.impact = ImpactService(db)
        self.sla = SlaService(db)
        self.commercial = CommercialService(db)

    async def get_revenue_per_min(self, incident_id: UUID) -> Metric:
        cells = await self.impact.get_affected_cells(incident_id)
        total = sum(float(c.revenue_per_min_azn) for c in cells)
        return Metric(
            value=total,
            unit="AZN/min",
            formula="sum(cell.revenue_per_min_azn for affected cells)",
            inputs={"affected_cell_count": len(cells)},
            sources=[SourceRef(table="cells", id=str(c.id)) for c in cells],
        )

    async def get_lost_revenue(self, incident_id: UUID, *, now: datetime | None = None) -> Metric:
        now = now or datetime.now(UTC)
        incident = await self.incidents.get_by_id(incident_id)
        revenue_per_min = await self.get_revenue_per_min(incident_id)
        projection_time = incident.eta_at or now
        minutes_elapsed = max(0.0, (projection_time - incident.started_at).total_seconds() / 60)
        lost = revenue_per_min.value * minutes_elapsed
        return Metric(
            value=lost,
            unit="AZN",
            formula="revenue_per_min_azn * minutes(started_at, eta_at or now)",
            inputs={
                "revenue_per_min_azn": revenue_per_min.value,
                "started_at": incident.started_at.isoformat(),
                "projection_time": projection_time.isoformat(),
                "minutes_elapsed": minutes_elapsed,
            },
            sources=revenue_per_min.sources,
        )

    async def get_projected_penalties(
        self, incident_id: UUID, *, now: datetime | None = None
    ) -> Metric:
        incident = await self.incidents.get_by_id(incident_id)
        contracts = await self.impact.get_affected_contracts(incident_id)
        slas = [
            await self.sla.get_contract_sla(incident_id, c, now=now) for c in contracts
        ]
        if incident.eta_at is not None:
            per_contract = [
                s.projected_penalty_at_eta_azn.value
                for s in slas
                if s.projected_penalty_at_eta_azn is not None
            ]
            formula = "sum(projected_penalty_at_eta_azn for affected contracts)"
        else:
            per_contract = [s.penalty_accrued_so_far_azn.value for s in slas]
            formula = "sum(penalty_accrued_so_far_azn for affected contracts) -- no ETA set yet"
        total = sum(per_contract)
        return Metric(
            value=total,
            unit="AZN",
            formula=formula,
            inputs={"contract_count": len(contracts)},
            sources=[SourceRef(table="contracts", id=str(c.id)) for c in contracts],
        )

    async def get_summary(
        self, incident_id: UUID, *, now: datetime | None = None
    ) -> FinanceSummaryOut:
        now = now or datetime.now(UTC)
        revenue_per_min = await self.get_revenue_per_min(incident_id)
        lost_revenue = await self.get_lost_revenue(incident_id, now=now)
        projected_penalties = await self.get_projected_penalties(incident_id, now=now)
        compensation_cost = await self.commercial.get_compensation_cost(incident_id)

        total_exposure_value = (
            lost_revenue.value + projected_penalties.value + compensation_cost.value
        )
        total_exposure = Metric(
            value=total_exposure_value,
            unit="AZN",
            formula="lost_revenue_azn + projected_penalties_azn + compensation_cost_azn",
            inputs={
                "lost_revenue_azn": lost_revenue.value,
                "projected_penalties_azn": projected_penalties.value,
                "compensation_cost_azn": compensation_cost.value,
            },
            sources=[],
        )

        return FinanceSummaryOut(
            incident_id=incident_id,
            revenue_per_min_azn=revenue_per_min,
            lost_revenue_azn=lost_revenue,
            projected_penalties_azn=projected_penalties,
            compensation_cost_azn=compensation_cost,
            total_exposure_azn=total_exposure,
        )
