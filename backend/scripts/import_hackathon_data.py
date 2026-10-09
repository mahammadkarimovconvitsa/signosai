"""One-off loader for a hand-off CSV dataset (telecom_hackathon_data.zip) into
the real database, following the load order in docs/DATA_SCHEMA.md.

The dataset is missing two things the schema needs, handled here explicitly
rather than silently:

1. No cells.csv. subscriber_segments.cell_id / subscribers.home_cell_id are
   literally site ids (verified: 100% overlap, 1 cell's worth of ids per
   site) -- the generator treated site and cell as 1:1. We synthesize one
   Cell per site reusing the site's id as the cell id, so every existing FK
   reference resolves with no remapping. technology and revenue_per_min_azn
   aren't in the source data at all; both are a deterministic function of the
   site id (reproducible, not random each run), documented inline below.
   These numbers feed the demo's finance figures directly -- replace them
   with real values when available.
2. users.hashed_password is the literal string "hashed_password_mock" for
   every row -- not a real hash, these accounts could never log in as
   imported. We hash a known dev password (see DEV_PASSWORD below) for all
   of them instead and print it once at the end.

Run:
    docker compose exec api python scripts/import_hackathon_data.py /tmp/hackathon_data
"""

import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.business_config import BusinessConfig  # noqa: E402
from app.models.cell import Cell  # noqa: E402
from app.models.contract import Contract  # noqa: E402
from app.models.customer import CustomerSite, EnterpriseCustomer  # noqa: E402
from app.models.enums import (  # noqa: E402
    CellTechnology,
    ContractType,
    CustomerServiceType,
    LinkType,
    MarketItemType,
    OperationalStatus,
    SubscriberSegment,
    UserRole,
)
from app.models.link import Link  # noqa: E402
from app.models.market_item import MarketItem  # noqa: E402
from app.models.runbook import Runbook  # noqa: E402
from app.models.site import Site  # noqa: E402
from app.models.subscriber import Subscriber, SubscriberSegmentCount  # noqa: E402
from app.models.user import User  # noqa: E402

DEV_PASSWORD = "Telecom123!"  # noqa: S105 -- disclosed dev-only password, not a secret


def parse_bool(v: str) -> bool:
    return v.strip().lower() == "true"


def parse_dt(v: str) -> datetime:
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def parse_date(v: str) -> date | None:
    return date.fromisoformat(v) if v else None


def rows(path: Path, name: str) -> list[dict]:
    with (path / name).open(newline="") as f:
        return list(csv.DictReader(f))


def cell_technology_for_site(site_id: str) -> CellTechnology:
    # Deterministic, not random: same input always produces the same output.
    digest = hashlib.sha256(site_id.encode()).hexdigest()
    return CellTechnology.FIVE_G if int(digest[0], 16) % 2 == 0 else CellTechnology.FOUR_G


def revenue_per_min_for_site(site_id: str) -> float:
    # AZN 8-40/min, deterministic from the site id -- plausible range matching
    # the scale used elsewhere in this project's demo scenarios, not a real
    # usage-derived figure. Replace once real per-cell revenue data exists.
    digest = hashlib.sha256((site_id + "revenue").encode()).hexdigest()
    span = int(digest[:8], 16) / 0xFFFFFFFF  # 0..1
    return round(8 + span * 32, 2)


async def main(data_dir: Path) -> None:
    async with AsyncSessionLocal() as db:
        print("Loading CSVs...")
        users_rows = rows(data_dir, "users.csv")
        sites_rows = rows(data_dir, "sites.csv")
        links_rows = rows(data_dir, "links.csv")
        seg_rows = rows(data_dir, "subscriber_segments.csv")
        sub_rows = rows(data_dir, "subscribers.csv")
        cust_rows = rows(data_dir, "enterprise_customers.csv")
        custsite_rows = rows(data_dir, "customer_sites.csv")
        contract_rows = rows(data_dir, "contracts.csv")
        runbook_rows = rows(data_dir, "runbooks.csv")
        market_rows = rows(data_dir, "market_items.csv")

        # 1. users -- real bcrypt hash for a disclosed dev password, not the
        # placeholder "hashed_password_mock" from the source file.
        print(f"users: {len(users_rows)}")
        dev_hash = hash_password(DEV_PASSWORD)
        for r in users_rows:
            existing = await db.scalar(select(User).where(User.id == UUID(r["id"])))
            if existing:
                continue
            db.add(
                User(
                    id=UUID(r["id"]),
                    email=r["email"],
                    hashed_password=dev_hash,
                    role=UserRole(r["role"]),
                    is_active=parse_bool(r["is_active"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 2. sites, uplink_link_id left NULL for now (circular FK with links)
        print(f"sites: {len(sites_rows)}")
        for r in sites_rows:
            db.add(
                Site(
                    id=UUID(r["id"]),
                    name=r["name"],
                    lat=float(r["lat"]),
                    lng=float(r["lng"]),
                    district=r["district"],
                    uplink_link_id=None,
                    energy_cost_azn_month=float(r["energy_cost_azn_month"]),
                    status=OperationalStatus(r["status"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 3. links -- now the sites they reference exist
        print(f"links: {len(links_rows)}")
        for r in links_rows:
            db.add(
                Link(
                    id=UUID(r["id"]),
                    from_site_id=UUID(r["from_site_id"]),
                    to_site_id=UUID(r["to_site_id"]),
                    type=LinkType(r["type"]),
                    is_protected=parse_bool(r["is_protected"]),
                    status=OperationalStatus(r["status"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 4. backfill sites.uplink_link_id
        print("backfilling sites.uplink_link_id...")
        for r in sites_rows:
            if r["uplink_link_id"]:
                site = await db.get(Site, UUID(r["id"]))
                site.uplink_link_id = UUID(r["uplink_link_id"])
        await db.flush()

        # 5. cells -- synthesized 1:1 with sites, see module docstring
        print(f"cells (synthesized 1:1 with sites): {len(sites_rows)}")
        for r in sites_rows:
            db.add(
                Cell(
                    id=UUID(r["id"]),
                    site_id=UUID(r["id"]),
                    technology=cell_technology_for_site(r["id"]),
                    revenue_per_min_azn=revenue_per_min_for_site(r["id"]),
                    status=OperationalStatus(r["status"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 6. subscriber_segments, subscribers -- cell_id already lines up
        print(f"subscriber_segments: {len(seg_rows)}")
        for r in seg_rows:
            db.add(
                SubscriberSegmentCount(
                    id=UUID(r["id"]),
                    cell_id=UUID(r["cell_id"]),
                    segment=SubscriberSegment(r["segment"]),
                    count=int(r["count"]),
                    arpu_azn=float(r["arpu_azn"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )

        print(f"subscribers: {len(sub_rows)}")
        for r in sub_rows:
            db.add(
                Subscriber(
                    id=UUID(r["id"]),
                    home_cell_id=UUID(r["home_cell_id"]),
                    segment=SubscriberSegment(r["segment"]),
                    msisdn_masked=r["msisdn_masked"],
                    name=r["name"] or None,
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 7. enterprise_customers
        print(f"enterprise_customers: {len(cust_rows)}")
        for r in cust_rows:
            db.add(
                EnterpriseCustomer(
                    id=UUID(r["id"]),
                    name=r["name"],
                    sector=r["sector"],
                    account_manager_user_id=UUID(r["account_manager_user_id"])
                    if r["account_manager_user_id"]
                    else None,
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 8. customer_sites, contracts
        print(f"customer_sites: {len(custsite_rows)}")
        for r in custsite_rows:
            db.add(
                CustomerSite(
                    id=UUID(r["id"]),
                    customer_id=UUID(r["customer_id"]),
                    site_id=UUID(r["site_id"]),
                    service_type=CustomerServiceType(r["service_type"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )

        print(f"contracts: {len(contract_rows)}")
        for r in contract_rows:
            db.add(
                Contract(
                    id=UUID(r["id"]),
                    customer_id=UUID(r["customer_id"]),
                    type=ContractType(r["type"]),
                    restore_within_min=int(r["restore_within_min"]),
                    penalty_per_started_hour_azn=float(r["penalty_per_started_hour_azn"]),
                    penalty_cap_azn=float(r["penalty_cap_azn"]),
                    clause_text=r["clause_text"],
                    valid_from=parse_date(r["valid_from"]),
                    valid_to=parse_date(r["valid_to"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )
        await db.flush()

        # 9. runbooks, market_items (independent of everything above)
        print(f"runbooks: {len(runbook_rows)}")
        for r in runbook_rows:
            db.add(
                Runbook(
                    id=UUID(r["id"]),
                    title=r["title"],
                    failure_type=r["failure_type"],
                    steps=json.loads(r["steps"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )

        print(f"market_items: {len(market_rows)}")
        for r in market_rows:
            db.add(
                MarketItem(
                    id=UUID(r["id"]),
                    type=MarketItemType(r["type"]),
                    title=r["title"],
                    summary=r["summary"],
                    source=r["source"],
                    published_at=parse_dt(r["published_at"]),
                    created_at=parse_dt(r["created_at"]),
                    updated_at=parse_dt(r["updated_at"]),
                )
            )

        await db.commit()
        print("Done.")
        print(f"\nAll imported users share the dev password: {DEV_PASSWORD}")

        # business_config.csv wasn't in the dataset -- confirm that's really
        # empty rather than silently skipping something that was there.
        bc_count = await db.scalar(select(BusinessConfig))
        if bc_count is None:
            print("Note: no business_config.csv in the dataset -- table left empty (code defaults apply).")


if __name__ == "__main__":
    import asyncio

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/hackathon_data")
    asyncio.run(main(data_dir))
