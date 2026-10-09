import uuid

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LinkType, OperationalStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Link(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "links"

    from_site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    to_site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    type: Mapped[LinkType] = mapped_column(pg_enum(LinkType, "link_type"), nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[OperationalStatus] = mapped_column(
        pg_enum(OperationalStatus, "operational_status"),
        nullable=False,
        default=OperationalStatus.UP,
    )
