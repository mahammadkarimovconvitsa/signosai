from typing import Generic, TypeVar

from pydantic import BaseModel

V = TypeVar("V")


class SourceRef(BaseModel):
    table: str
    id: str


class Metric(BaseModel, Generic[V]):
    """A computed number with its full provenance — the 'why this number' contract.

    Every business figure (SLA deadline, penalty, revenue loss, exposure, ...) is
    returned as one of these instead of a bare number, so the frontend's
    "why this number" drawer and the /explain endpoint never need a second code path.
    """

    value: V
    unit: str
    formula: str
    inputs: dict
    sources: list[SourceRef]
