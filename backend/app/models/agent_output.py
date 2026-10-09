import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ActionAgent, AgentOutputSource
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class AgentOutput(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "agent_outputs"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    agent: Mapped[ActionAgent] = mapped_column(
        pg_enum(ActionAgent, "action_agent"), nullable=False
    )
    output: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[AgentOutputSource] = mapped_column(
        pg_enum(AgentOutputSource, "agent_output_source"), nullable=False
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
