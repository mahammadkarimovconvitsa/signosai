import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ActionAgent, ActionStatus, RiskLevel, UserRole
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Action(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "actions"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    agent: Mapped[ActionAgent] = mapped_column(
        pg_enum(ActionAgent, "action_agent"), nullable=False
    )
    proposal: Mapped[str] = mapped_column(Text, nullable=False)
    owner_role: Mapped[UserRole] = mapped_column(pg_enum(UserRole, "user_role"), nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        pg_enum(ActionStatus, "action_status"), nullable=False, default=ActionStatus.PROPOSED
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        pg_enum(RiskLevel, "risk_level"), nullable=False, default=RiskLevel.MEDIUM
    )
    # list[{"table": str, "id": str}] — traceability pointers into source rows.
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
