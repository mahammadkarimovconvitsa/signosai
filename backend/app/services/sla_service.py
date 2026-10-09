import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.enums import ComplianceStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.customer import EnterpriseCustomerOut
from app.schemas.impact import CustomerImpactOut
from app.schemas.metric import Metric, SourceRef
from app.schemas.sla import ContractSlaOut
from app.services.config_service import ConfigService
from app.services.impact_service import ImpactService

DEFAULT_AT_RISK_THRESHOLD_MIN = "60"


def _penalty_for_hours_over(hours_over: float, rate: float, cap: float) -> float:
    """'min(cap, ceil(hours_over) x rate)' — partial hours bill as a full hour."""
    if hours_over <= 0:
        return 0.0
    billed_hours = math.ceil(hours_over)
    return min(cap, billed_hours * rate)


class SlaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.incidents = IncidentRepository(db)
        self.impact = ImpactService(db)
        self.customers = CustomerRepository(db)
        self.config = ConfigService(db)

    async def get_contract_sla(
        self, incident_id: UUID, contract: Contract, *, now: datetime | None = None
    ) -> ContractSlaOut:
        incident = await self.incidents.get_by_id(incident_id)
        now = now or datetime.now(UTC)

        deadline = incident.started_at + timedelta(minutes=contract.restore_within_min)
        remaining_min = (deadline - now).total_seconds() / 60

        threshold_min = float(
            await self.config.get_value(
                "sla_at_risk_threshold_min", DEFAULT_AT_RISK_THRESHOLD_MIN
            )
        )
        compliance = self._compliance_status(remaining_min, threshold_min)

        rate = float(contract.penalty_per_started_hour_azn)
        cap = float(contract.penalty_cap_azn)

        hours_over_now = (now - deadline).total_seconds() / 3600
        penalty_accrued_so_far = Metric(
            value=_penalty_for_hours_over(hours_over_now, rate, cap),
            unit="AZN",
            formula=(
                "min(penalty_cap_azn, "
                "ceil(max(0, (now - deadline) / 1h)) * penalty_per_started_hour_azn)"
            ),
            inputs={
                "now": now.isoformat(),
                "deadline": deadline.isoformat(),
                "penalty_per_started_hour_azn": rate,
                "penalty_cap_azn": cap,
            },
            sources=[SourceRef(table="contracts", id=str(contract.id))],
        )

        projected_penalty = None
        if incident.eta_at is not None:
            hours_over_eta = (incident.eta_at - deadline).total_seconds() / 3600
            projected_penalty = Metric(
                value=_penalty_for_hours_over(hours_over_eta, rate, cap),
                unit="AZN",
                formula=(
                    "min(penalty_cap_azn, "
                    "ceil(max(0, (eta_at - deadline) / 1h)) * penalty_per_started_hour_azn)"
                ),
                inputs={
                    "eta_at": incident.eta_at.isoformat(),
                    "deadline": deadline.isoformat(),
                    "penalty_per_started_hour_azn": rate,
                    "penalty_cap_azn": cap,
                },
                sources=[
                    SourceRef(table="incidents", id=str(incident.id)),
                    SourceRef(table="contracts", id=str(contract.id)),
                ],
            )

        return ContractSlaOut(
            contract_id=contract.id,
            customer_id=contract.customer_id,
            deadline=Metric(
                value=deadline.isoformat(),
                unit="timestamp",
                formula="incident.started_at + contract.restore_within_min",
                inputs={
                    "started_at": incident.started_at.isoformat(),
                    "restore_within_min": contract.restore_within_min,
                },
                sources=[
                    SourceRef(table="incidents", id=str(incident.id)),
                    SourceRef(table="contracts", id=str(contract.id)),
                ],
            ),
            time_remaining_min=Metric(
                value=remaining_min,
                unit="minutes",
                formula="deadline - now",
                inputs={"deadline": deadline.isoformat(), "now": now.isoformat()},
                sources=[SourceRef(table="contracts", id=str(contract.id))],
            ),
            compliance_status=compliance,
            penalty_accrued_so_far_azn=penalty_accrued_so_far,
            projected_penalty_at_eta_azn=projected_penalty,
            worst_case_penalty_azn=Metric(
                value=cap,
                unit="AZN",
                formula="contract.penalty_cap_azn",
                inputs={"penalty_cap_azn": cap},
                sources=[SourceRef(table="contracts", id=str(contract.id))],
            ),
        )

    async def get_incident_sla(
        self, incident_id: UUID, *, now: datetime | None = None
    ) -> list[ContractSlaOut]:
        contracts = await self.impact.get_affected_contracts(incident_id)
        return [await self.get_contract_sla(incident_id, c, now=now) for c in contracts]

    async def get_customer_impact(
        self, incident_id: UUID, *, now: datetime | None = None
    ) -> list[CustomerImpactOut]:
        customers = await self.impact.get_affected_customers(incident_id)
        results = []
        for customer in customers:
            contracts, _ = await self.impact.contracts.list_paginated(
                limit=500, offset=0, customer_id=customer.id
            )
            slas = [await self.get_contract_sla(incident_id, c, now=now) for c in contracts]
            results.append(
                CustomerImpactOut(
                    customer=EnterpriseCustomerOut.model_validate(customer), contracts=slas
                )
            )
        return results

    @staticmethod
    def _compliance_status(remaining_min: float, threshold_min: float) -> ComplianceStatus:
        if remaining_min <= 0:
            return ComplianceStatus.BREACHED
        if remaining_min <= threshold_min:
            return ComplianceStatus.AT_RISK
        return ComplianceStatus.OK
