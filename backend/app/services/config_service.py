from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.business_config import BusinessConfig
from app.models.enums import AutonomyLevel
from app.models.settings import Settings
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.business_config_repository import BusinessConfigRepository
from app.repositories.settings_repository import SettingsRepository


class ConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = SettingsRepository(db)
        self.business_config = BusinessConfigRepository(db)
        self.audit = AuditRepository(db)

    async def get_value(self, key: str, default: str) -> str:
        """Read-only, non-committing lookup for other services to compose mid-transaction.

        Falls back to `default` when the data engineer hasn't seeded this key yet,
        so calculations never crash on an empty business_config table — but the DB
        value always wins once it exists.
        """
        config = await self.business_config.get_by_key(key)
        return config.value if config is not None else default

    async def get_settings(self) -> Settings:
        settings = await self.settings.get_singleton()
        await self.db.commit()
        return settings

    async def update_settings(self, autonomy_level: AutonomyLevel, actor: User) -> Settings:
        settings = await self.settings.update_autonomy_level(autonomy_level)
        await self.audit.log(
            event_type="settings.updated",
            entity="settings",
            entity_id=settings.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
            details={"autonomy_level": autonomy_level.value},
        )
        await self.db.commit()
        return settings

    async def list_business_config(
        self, limit: int, offset: int
    ) -> tuple[list[BusinessConfig], int]:
        items, total = await self.business_config.list_paginated(limit, offset)
        await self.db.commit()
        return items, total

    async def get_business_config(self, key: str) -> BusinessConfig:
        config = await self.business_config.get_by_key(key)
        if config is None:
            raise NotFoundError(f"Business config key '{key}' not found")
        return config

    async def update_business_config(
        self, key: str, value: str, description: str | None, actor: User
    ) -> BusinessConfig:
        config = await self.business_config.upsert(key, value, description)
        await self.audit.log(
            event_type="business_config.updated",
            entity="business_config",
            entity_id=config.id,
            actor_user_id=actor.id,
            actor_role=actor.role,
            details={"key": key, "value": value},
        )
        await self.db.commit()
        return config
