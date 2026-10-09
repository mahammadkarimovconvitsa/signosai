import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import SubscriberSegment
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class SubscriberSegmentCount(UUIDPKMixin, TimestampMixin, Base):
    """Aggregated subscriber counts per cell per segment (not individual people)."""

    __tablename__ = "subscriber_segments"

    cell_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cells.id"), nullable=False, index=True
    )
    segment: Mapped[SubscriberSegment] = mapped_column(
        pg_enum(SubscriberSegment, "subscriber_segment"), nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    arpu_azn: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class Subscriber(UUIDPKMixin, TimestampMixin, Base):
    """Named individual subscribers, only populated for premium-segment lists."""

    __tablename__ = "subscribers"

    home_cell_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cells.id"), nullable=False, index=True
    )
    segment: Mapped[SubscriberSegment] = mapped_column(
        pg_enum(SubscriberSegment, "subscriber_segment"), nullable=False
    )
    msisdn_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
