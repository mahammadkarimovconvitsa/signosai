import enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.metric import Metric


class PortfolioRecommendation(str, enum.Enum):
    UPGRADE = "upgrade"
    KEEP = "keep"
    CONSOLIDATE = "consolidate"
    DECOMMISSION = "decommission"


class SitePortfolioOut(BaseModel):
    site_id: UUID
    site_name: str
    traffic_proxy_subscribers: Metric
    revenue_azn_month: Metric
    energy_cost_azn_month: Metric
    revenue_to_cost_ratio: Metric
    recommendation: PortfolioRecommendation
