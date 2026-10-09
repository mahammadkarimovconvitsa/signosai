"""Generates docs/schemas/*.json from the live SQLAlchemy models.

Run after any model change so the JSON Schemas handed to the data engineer
never drift from the real DB schema:

    docker compose exec api python scripts/export_schemas.py
"""

import json
import sys
from pathlib import Path

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.business_config import BusinessConfig
from app.models.cell import Cell
from app.models.contract import Contract
from app.models.customer import CustomerSite, EnterpriseCustomer
from app.models.link import Link
from app.models.market_item import MarketItem
from app.models.runbook import Runbook
from app.models.site import Site
from app.models.subscriber import Subscriber, SubscriberSegmentCount
from app.models.user import User

# Only engineer-populated (reference data) tables, per the spec.
ENGINEER_POPULATED_MODELS = [
    Site,
    Cell,
    Link,
    SubscriberSegmentCount,
    Subscriber,
    EnterpriseCustomer,
    CustomerSite,
    Contract,
    Runbook,
    MarketItem,
    BusinessConfig,
    User,
]

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "schemas"


def column_to_json_schema(col) -> dict:
    t = col.type
    schema: dict = {}

    if isinstance(t, UUID):
        schema = {"type": "string", "format": "uuid"}
    elif isinstance(t, Enum):
        schema = {"type": "string", "enum": [e for e in t.enums]}
    elif isinstance(t, String | Text):
        schema = {"type": "string"}
        if isinstance(t, String) and t.length:
            schema["maxLength"] = t.length
    elif isinstance(t, Boolean):
        schema = {"type": "boolean"}
    elif isinstance(t, Integer):
        schema = {"type": "integer"}
    elif isinstance(t, Numeric | Float):
        schema = {"type": "number"}
    elif isinstance(t, DateTime):
        schema = {"type": "string", "format": "date-time"}
    elif isinstance(t, Date):
        schema = {"type": "string", "format": "date"}
    elif isinstance(t, JSONB):
        schema = {"type": ["array", "object"]}
    else:
        schema = {"type": "string"}

    if col.nullable:
        schema["type"] = [schema["type"], "null"] if isinstance(schema["type"], str) else [
            *schema["type"],
            "null",
        ]
    return schema


def model_to_json_schema(model) -> dict:
    table = model.__table__
    properties = {}
    required = []

    for col in table.columns:
        properties[col.name] = column_to_json_schema(col)
        # Only server_default counts here, not the ORM-side `default=` — the
        # data engineer loads via raw SQL/COPY, not through the app's ORM, so
        # a Python-side default (e.g. status=UP) never applies to their
        # inserts and the column is required in practice.
        if not col.nullable and col.server_default is None:
            required.append(col.name)

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": table.name,
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in ENGINEER_POPULATED_MODELS:
        schema = model_to_json_schema(model)
        out_path = OUT_DIR / f"{model.__table__.name}.schema.json"
        out_path.write_text(json.dumps(schema, indent=2) + "\n")
        print(f"wrote {out_path.relative_to(OUT_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
