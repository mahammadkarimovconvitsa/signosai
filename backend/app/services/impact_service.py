from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cell import Cell
from app.models.contract import Contract
from app.models.customer import CustomerSite, EnterpriseCustomer
from app.repositories.contract_repository import ContractRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.network_repository import CellRepository


class ImpactService:
    """Walks the sites -> cells -> customers -> contracts chain for an incident.

    This is the join logic SLA/Finance/Commercial all build on, kept in one place
    so "who and what is affected" has a single definition.
    """

    def __init__(self, db: AsyncSession):
        self.incidents = IncidentRepository(db)
        self.cells = CellRepository(db)
        self.customers = CustomerRepository(db)
        self.contracts = ContractRepository(db)

    async def get_affected_site_ids(self, incident_id: UUID) -> list[UUID]:
        affected = await self.incidents.list_affected_sites(incident_id)
        return [a.site_id for a in affected]

    async def get_affected_cells(self, incident_id: UUID) -> list[Cell]:
        site_ids = await self.get_affected_site_ids(incident_id)
        return await self.cells.list_for_sites(site_ids)

    async def get_affected_customers(self, incident_id: UUID) -> list[EnterpriseCustomer]:
        site_ids = await self.get_affected_site_ids(incident_id)
        return await self.customers.list_customers_for_sites(site_ids)

    async def get_affected_customer_sites(self, incident_id: UUID) -> list[CustomerSite]:
        site_ids = await self.get_affected_site_ids(incident_id)
        return await self.customers.list_customer_sites_for_sites(site_ids)

    async def get_affected_contracts(self, incident_id: UUID) -> list[Contract]:
        customers = await self.get_affected_customers(incident_id)
        return await self.contracts.list_by_customer_ids([c.id for c in customers])
