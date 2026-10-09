from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MarketItemType
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class MarketItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "market_items"

    type: Mapped[MarketItemType] = mapped_column(
        pg_enum(MarketItemType, "market_item_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
