from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import CellTechnology, LinkType, OperationalStatus


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    lat: float
    lng: float
    district: str
    uplink_link_id: UUID | None
    energy_cost_azn_month: float
    status: OperationalStatus


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_site_id: UUID
    to_site_id: UUID
    type: LinkType
    is_protected: bool
    status: OperationalStatus


class CellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    technology: CellTechnology
    revenue_per_min_azn: float
    status: OperationalStatus
