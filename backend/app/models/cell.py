import uuid

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CellTechnology, OperationalStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Cell(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "cells"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    technology: Mapped[CellTechnology] = mapped_column(
        pg_enum(CellTechnology, "cell_technology"), nullable=False
    )
    revenue_per_min_azn: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    status: Mapped[OperationalStatus] = mapped_column(
        pg_enum(OperationalStatus, "operational_status"),
        nullable=False,
        default=OperationalStatus.UP,
    )
