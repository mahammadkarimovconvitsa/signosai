from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.cell import Cell
from app.models.link import Link
from app.models.site import Site
from app.repositories.network_repository import CellRepository, LinkRepository, SiteRepository


class NetworkService:
    def __init__(self, db: AsyncSession):
        self.sites = SiteRepository(db)
        self.links = LinkRepository(db)
        self.cells = CellRepository(db)

    async def list_sites(self, limit: int, offset: int) -> tuple[list[Site], int]:
        return await self.sites.list_paginated(limit, offset)

    async def get_site(self, site_id: UUID) -> Site:
        site = await self.sites.get_by_id(site_id)
        if site is None:
            raise NotFoundError(f"Site {site_id} not found")
        return site

    async def list_links(self, limit: int, offset: int) -> tuple[list[Link], int]:
        return await self.links.list_paginated(limit, offset)

    async def list_cells(
        self, limit: int, offset: int, site_id: UUID | None = None
    ) -> tuple[list[Cell], int]:
        return await self.cells.list_paginated(limit, offset, site_id)
