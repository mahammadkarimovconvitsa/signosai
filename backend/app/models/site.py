import uuid

from sqlalchemy import Float, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OperationalStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Site(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sites"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    district: Mapped[str] = mapped_column(String(255), nullable=False)
    uplink_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("links.id", use_alter=True, name="fk_sites_uplink_link_id"),
        nullable=True,
    )
    energy_cost_azn_month: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[OperationalStatus] = mapped_column(
        pg_enum(OperationalStatus, "operational_status"),
        nullable=False,
        default=OperationalStatus.UP,
    )
