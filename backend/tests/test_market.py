from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MarketItemType, UserRole
from app.models.market_item import MarketItem
from tests.helpers import auth_headers

pytestmark = pytest.mark.asyncio


async def test_list_market_items(client: AsyncClient, db_session: AsyncSession):
    item = MarketItem(
        type=MarketItemType.REGULATOR,
        title="Spectrum auction announced",
        summary="Regulator announces 700MHz auction.",
        source="Ministry of Digital Development",
        published_at=datetime.now(UTC),
    )
    db_session.add(item)
    await db_session.commit()

    headers = await auth_headers(client, db_session, "viewer@signos.app", UserRole.VIEWER)
    resp = await client.get("/api/v1/market", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
