import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ContractType
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Contract(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "contracts"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enterprise_customers.id"), nullable=False, index=True
    )
    type: Mapped[ContractType] = mapped_column(
        pg_enum(ContractType, "contract_type"), nullable=False
    )
    restore_within_min: Mapped[int] = mapped_column(Integer, nullable=False)
    penalty_per_started_hour_azn: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    penalty_cap_azn: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
