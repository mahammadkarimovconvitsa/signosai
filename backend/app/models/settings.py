from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AutonomyLevel
from app.models.mixins import TimestampMixin, UUIDPKMixin, pg_enum


class Settings(UUIDPKMixin, TimestampMixin, Base):
    """Singleton table — the service layer ensures exactly one row ever exists."""

    __tablename__ = "settings"

    autonomy_level: Mapped[AutonomyLevel] = mapped_column(
        pg_enum(AutonomyLevel, "autonomy_level"),
        nullable=False,
        default=AutonomyLevel.RECOMMEND_ONLY,
    )
