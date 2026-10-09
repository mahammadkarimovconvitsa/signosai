import enum
import uuid
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


@lru_cache
def pg_enum(enum_cls: type[enum.Enum], name: str) -> Enum:
    # Cached so every column referencing the same enum name reuses one Enum
    # instance, instead of SQLAlchemy trying to CREATE TYPE it more than once.
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
