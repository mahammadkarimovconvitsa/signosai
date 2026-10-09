import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CustomerServiceType
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class EnterpriseCustomer(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "enterprise_customers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(255), nullable=False)
    account_manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class CustomerSite(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "customer_sites"
    __table_args__ = (
        UniqueConstraint("customer_id", "site_id", "service_type", name="uq_customer_site_service"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enterprise_customers.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    service_type: Mapped[CustomerServiceType] = mapped_column(
        pg_enum(CustomerServiceType, "customer_service_type"), nullable=False
    )
