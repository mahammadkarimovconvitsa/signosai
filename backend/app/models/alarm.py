import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AlarmSeverity
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Alarm(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "alarms"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    cell_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cells.id"), nullable=True
    )
    link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("links.id"), nullable=True
    )
    severity: Mapped[AlarmSeverity] = mapped_column(
        pg_enum(AlarmSeverity, "alarm_severity"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True
    )
