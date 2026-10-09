import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LinkType, OperationalStatus, UserRole
from app.models.link import Link
from app.models.site import Site
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def _seed_site_pair(db_session: AsyncSession) -> tuple[Site, Site, Link]:
    site_a = Site(
        name="Site A",
        lat=40.4,
        lng=49.8,
        district="Nasimi",
        energy_cost_azn_month=500,
        status=OperationalStatus.UP,
    )
    site_b = Site(
        name="Site B",
        lat=40.5,
        lng=49.9,
        district="Binagadi",
        energy_cost_azn_month=600,
        status=OperationalStatus.DOWN,
    )
    db_session.add_all([site_a, site_b])
    await db_session.flush()

    link = Link(
        from_site_id=site_a.id,
        to_site_id=site_b.id,
        type=LinkType.FIBER,
        is_protected=False,
        status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(site_a)
    await db_session.refresh(site_b)
    await db_session.refresh(link)
    return site_a, site_b, link


async def test_list_sites_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/network/sites")
    assert resp.status_code == 401


async def test_list_sites(client: AsyncClient, db_session: AsyncSession):
    await _seed_site_pair(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get("/api/v1/network/sites", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


async def test_get_site_detail(client: AsyncClient, db_session: AsyncSession):
    site_a, _, _ = await _seed_site_pair(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(f"/api/v1/network/sites/{site_a.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Site A"


async def test_get_site_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        "/api/v1/network/sites/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404


async def test_list_links(client: AsyncClient, db_session: AsyncSession):
    await _seed_site_pair(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get("/api/v1/network/links", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_list_cells_filter_by_site(client: AsyncClient, db_session: AsyncSession):
    site_a, site_b, _ = await _seed_site_pair(db_session)
    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get(
        "/api/v1/network/cells", params={"site_id": str(site_a.id)}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
