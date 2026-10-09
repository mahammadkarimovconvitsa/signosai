import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import IncidentStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Incident(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "incidents"

    root_cause_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("links.id"), nullable=False
    )
    root_cause_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        pg_enum(IncidentStatus, "incident_status"), nullable=False, default=IncidentStatus.OPEN
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    eta_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IncidentAffectedSite(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "incident_affected_sites"
    __table_args__ = (UniqueConstraint("incident_id", "site_id", name="uq_incident_site"),)

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )


class IncidentTimelineEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "incident_timeline_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
