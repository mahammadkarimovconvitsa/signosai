from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import MarketItemType


class MarketItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: MarketItemType
    title: str
    summary: str
    source: str
    published_at: datetime
