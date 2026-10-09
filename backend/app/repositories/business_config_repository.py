from sqlalchemy import select

from app.models.business_config import BusinessConfig
from app.repositories.base import BaseRepository


class BusinessConfigRepository(BaseRepository):
    async def list_paginated(self, limit: int, offset: int) -> tuple[list[BusinessConfig], int]:
        stmt = select(BusinessConfig).order_by(BusinessConfig.key)
        return await self.paginate(stmt, limit, offset)

    async def get_by_key(self, key: str) -> BusinessConfig | None:
        result = await self.db.execute(select(BusinessConfig).where(BusinessConfig.key == key))
        return result.scalar_one_or_none()

    async def upsert(self, key: str, value: str, description: str | None) -> BusinessConfig:
        config = await self.get_by_key(key)
        if config is None:
            config = BusinessConfig(key=key, value=value, description=description)
            self.db.add(config)
        else:
            config.value = value
            if description is not None:
                config.description = description
        await self.db.flush()
        await self.db.refresh(config)
        return config
