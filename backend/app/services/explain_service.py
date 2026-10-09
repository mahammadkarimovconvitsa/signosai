from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.contract_repository import ContractRepository
from app.repositories.network_repository import SiteRepository
from app.schemas.metric import Metric
from app.services.commercial_service import CommercialService
from app.services.finance_service import FinanceService
from app.services.portfolio_service import PortfolioService
from app.services.sla_service import SlaService

SLA_FIELDS = {
    "deadline": "deadline",
    "time_remaining": "time_remaining_min",
    "penalty_accrued": "penalty_accrued_so_far_azn",
    "projected_penalty_at_eta": "projected_penalty_at_eta_azn",
    "worst_case_penalty": "worst_case_penalty_azn",
}
PORTFOLIO_FIELDS = {
    "traffic": "traffic_proxy_subscribers",
    "revenue": "revenue_azn_month",
    "energy_cost": "energy_cost_azn_month",
    "ratio": "revenue_to_cost_ratio",
}


class ExplainService:
    """Metrics aren't persisted rows — a metric id encodes how to recompute one.

    Format: "<domain>.<field>:<param1>[:<param2>]", e.g.
    "finance.total_exposure:<incident_id>" or "sla.deadline:<incident_id>:<contract_id>".
    Re-dispatches to the exact same service methods that produced the number on
    screen, so explain() can never drift from what the UI actually displayed.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def explain(self, metric_id: str) -> Metric:
        if ":" not in metric_id:
            raise ValidationAppError(f"Malformed metric id '{metric_id}'")
        kind, _, param_str = metric_id.partition(":")
        params = param_str.split(":")

        try:
            if kind == "finance.revenue_per_min":
                return await FinanceService(self.db).get_revenue_per_min(UUID(params[0]))
            if kind == "finance.lost_revenue":
                return await FinanceService(self.db).get_lost_revenue(UUID(params[0]))
            if kind == "finance.projected_penalties":
                return await FinanceService(self.db).get_projected_penalties(UUID(params[0]))
            if kind == "finance.total_exposure":
                summary = await FinanceService(self.db).get_summary(UUID(params[0]))
                return summary.total_exposure_azn
            if kind == "commercial.affected_premium_subscribers":
                return await CommercialService(self.db).get_affected_premium_count(UUID(params[0]))
            if kind == "commercial.compensation_cost":
                return await CommercialService(self.db).get_compensation_cost(UUID(params[0]))
            if kind.startswith("sla."):
                return await self._explain_sla(kind.removeprefix("sla."), params)
            if kind.startswith("portfolio."):
                return await self._explain_portfolio(kind.removeprefix("portfolio."), params)
        except (ValueError, IndexError) as exc:
            raise ValidationAppError(f"Malformed metric id '{metric_id}'") from exc

        raise NotFoundError(f"Unknown metric kind '{kind}'")

    async def _explain_sla(self, field: str, params: list[str]) -> Metric:
        if field not in SLA_FIELDS:
            raise NotFoundError(f"Unknown SLA metric field '{field}'")
        incident_id, contract_id = UUID(params[0]), UUID(params[1])
        contract = await ContractRepository(self.db).get_by_id(contract_id)
        if contract is None:
            raise NotFoundError(f"Contract {contract_id} not found")
        sla = await SlaService(self.db).get_contract_sla(incident_id, contract)
        metric = getattr(sla, SLA_FIELDS[field])
        if metric is None:
            raise NotFoundError(f"SLA metric '{field}' is not available (e.g. no ETA set yet)")
        return metric

    async def _explain_portfolio(self, field: str, params: list[str]) -> Metric:
        if field not in PORTFOLIO_FIELDS:
            raise NotFoundError(f"Unknown portfolio metric field '{field}'")
        site = await SiteRepository(self.db).get_by_id(UUID(params[0]))
        if site is None:
            raise NotFoundError(f"Site {params[0]} not found")
        out = await PortfolioService(self.db).get_site_portfolio(site)
        return getattr(out, PORTFOLIO_FIELDS[field])
