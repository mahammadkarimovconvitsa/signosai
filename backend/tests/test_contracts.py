from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.customer import EnterpriseCustomer
from app.models.enums import ContractType, UserRole
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def _seed_contract(db_session: AsyncSession) -> Contract:
    customer = EnterpriseCustomer(name="Bank HQ", sector="finance")
    db_session.add(customer)
    await db_session.flush()

    contract = Contract(
        customer_id=customer.id,
        type=ContractType.ENTERPRISE_SLA,
        restore_within_min=180,
        penalty_per_started_hour_azn=2000,
        penalty_cap_azn=30000,
        clause_text="Restore within 3 hours or pay penalty.",
        valid_from=date(2026, 1, 1),
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


async def test_list_contracts(client: AsyncClient, db_session: AsyncSession):
    await _seed_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get("/api/v1/contracts", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_get_contract_detail(client: AsyncClient, db_session: AsyncSession):
    contract = await _seed_contract(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(f"/api/v1/contracts/{contract.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["penalty_cap_azn"] == 30000
