from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Runbook(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "runbooks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    steps: Mapped[list] = mapped_column(JSONB, nullable=False)
