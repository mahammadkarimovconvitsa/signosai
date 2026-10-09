from sqlalchemy import select

from app.models.enums import AutonomyLevel
from app.models.settings import Settings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    async def get_singleton(self) -> Settings:
        result = await self.db.execute(select(Settings).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = Settings(autonomy_level=AutonomyLevel.RECOMMEND_ONLY)
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
        return settings

    async def update_autonomy_level(self, autonomy_level: AutonomyLevel) -> Settings:
        settings = await self.get_singleton()
        settings.autonomy_level = autonomy_level
        await self.db.flush()
        await self.db.refresh(settings)
        return settings
