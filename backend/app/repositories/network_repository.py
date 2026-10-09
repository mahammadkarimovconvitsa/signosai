from uuid import UUID

from sqlalchemy import select

from app.models.cell import Cell
from app.models.enums import OperationalStatus
from app.models.link import Link
from app.models.site import Site
from app.repositories.base import BaseRepository


class SiteRepository(BaseRepository):
    async def list_paginated(self, limit: int, offset: int) -> tuple[list[Site], int]:
        return await self.paginate(select(Site).order_by(Site.name), limit, offset)

    async def get_by_id(self, site_id: UUID) -> Site | None:
        return await self.db.get(Site, site_id)

    async def get_many(self, site_ids: list[UUID]) -> list[Site]:
        if not site_ids:
            return []
        result = await self.db.execute(select(Site).where(Site.id.in_(site_ids)))
        return list(result.scalars().all())

    async def list_by_uplink_link(self, link_id: UUID) -> list[Site]:
        result = await self.db.execute(select(Site).where(Site.uplink_link_id == link_id))
        return list(result.scalars().all())

    async def set_status(self, site: Site, status: OperationalStatus) -> Site:
        site.status = status
        await self.db.flush()
        return site


class LinkRepository(BaseRepository):
    async def list_paginated(self, limit: int, offset: int) -> tuple[list[Link], int]:
        return await self.paginate(select(Link).order_by(Link.created_at), limit, offset)

    async def get_by_id(self, link_id: UUID) -> Link | None:
        return await self.db.get(Link, link_id)

    async def set_status(self, link: Link, status: OperationalStatus) -> Link:
        link.status = status
        await self.db.flush()
        return link


class CellRepository(BaseRepository):
    async def list_paginated(
        self, limit: int, offset: int, site_id: UUID | None = None
    ) -> tuple[list[Cell], int]:
        stmt = select(Cell).order_by(Cell.created_at)
        if site_id is not None:
            stmt = stmt.where(Cell.site_id == site_id)
        return await self.paginate(stmt, limit, offset)

    async def get_by_id(self, cell_id: UUID) -> Cell | None:
        return await self.db.get(Cell, cell_id)

    async def list_for_sites(self, site_ids: list[UUID]) -> list[Cell]:
        if not site_ids:
            return []
        result = await self.db.execute(select(Cell).where(Cell.site_id.in_(site_ids)))
        return list(result.scalars().all())
