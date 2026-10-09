from uuid import UUID

from sqlalchemy import select

from app.models.customer import CustomerSite, EnterpriseCustomer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    async def get_by_id(self, customer_id: UUID) -> EnterpriseCustomer | None:
        return await self.db.get(EnterpriseCustomer, customer_id)

    async def list_customers_for_sites(self, site_ids: list[UUID]) -> list[EnterpriseCustomer]:
        if not site_ids:
            return []
        stmt = (
            select(EnterpriseCustomer)
            .join(CustomerSite, CustomerSite.customer_id == EnterpriseCustomer.id)
            .where(CustomerSite.site_id.in_(site_ids))
            .distinct()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_customer_sites_for_sites(self, site_ids: list[UUID]) -> list[CustomerSite]:
        if not site_ids:
            return []
        stmt = select(CustomerSite).where(CustomerSite.site_id.in_(site_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
