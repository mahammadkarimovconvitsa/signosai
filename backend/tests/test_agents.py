from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_client import GeminiCallResult
from app.models.cell import Cell
from app.models.contract import Contract
from app.models.customer import CustomerSite, EnterpriseCustomer
from app.models.enums import (
    ActionAgent,
    ActionStatus,
    AutonomyLevel,
    CellTechnology,
    ContractType,
    CustomerServiceType,
    IncidentStatus,
    LinkType,
    OperationalStatus,
    SubscriberSegment,
)
from app.models.incident import Incident, IncidentAffectedSite
from app.models.link import Link
from app.models.settings import Settings
from app.models.site import Site
from app.models.subscriber import SubscriberSegmentCount
from app.repositories.action_repository import ActionRepository
from app.repositories.agent_output_repository import AgentOutputRepository
from app.services.agent_orchestration_service import AgentOrchestrationService

pytestmark = pytest.mark.asyncio


async def _seed_incident(db_session: AsyncSession) -> Incident:
    site = Site(
        name="S", lat=40.4, lng=49.8, district="Nasimi",
        energy_cost_azn_month=500, status=OperationalStatus.DOWN,
    )
    db_session.add(site)
    await db_session.flush()
    link = Link(
        from_site_id=site.id, to_site_id=site.id, type=LinkType.FIBER,
        is_protected=False, status=OperationalStatus.DOWN,
    )
    db_session.add(link)
    await db_session.flush()
    cell = Cell(
        site_id=site.id, technology=CellTechnology.FOUR_G,
        revenue_per_min_azn=10, status=OperationalStatus.DOWN,
    )
    db_session.add(cell)
    await db_session.flush()
    db_session.add(
        SubscriberSegmentCount(
            cell_id=cell.id, segment=SubscriberSegment.PREMIUM, count=100, arpu_azn=50
        )
    )
    customer = EnterpriseCustomer(name="Bank HQ", sector="finance")
    db_session.add(customer)
    await db_session.flush()
    db_session.add(
        CustomerSite(
            customer_id=customer.id, site_id=site.id, service_type=CustomerServiceType.LEASED_LINE
        )
    )
    contract = Contract(
        customer_id=customer.id, type=ContractType.ENTERPRISE_SLA,
        restore_within_min=180, penalty_per_started_hour_azn=2000, penalty_cap_azn=30000,
        clause_text="Restore within 3 hours.", valid_from=date(2026, 1, 1),
    )
    db_session.add(contract)
    await db_session.flush()
    incident = Incident(
        root_cause_link_id=link.id, root_cause_summary="Fiber cut",
        status=IncidentStatus.OPEN, started_at=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.flush()
    db_session.add(IncidentAffectedSite(incident_id=incident.id, site_id=site.id))
    await db_session.commit()
    await db_session.refresh(incident)
    return incident


def _mock_result(data: dict) -> GeminiCallResult:
    return GeminiCallResult(data=data, model="gemini-2.0-flash", tokens=42)


async def test_successful_agent_run_stores_output_and_creates_action(db_session: AsyncSession):
    incident = await _seed_incident(db_session)

    with (
        patch(
            "app.services.agents.network_agent.generate_structured",
            new=AsyncMock(
                return_value=_mock_result(
                    {
                        "summary": "Fiber cut explained",
                        "root_cause": "FL-07 down",
                        "runbook": ["Step 1"],
                    }
                )
            ),
        ),
        patch(
            "app.services.agents.contracts_agent.generate_structured",
            new=AsyncMock(
                return_value=_mock_result(
                    {"summary": "Bank HQ SLA at risk", "obligations": ["Restore within 3h"]}
                )
            ),
        ),
        patch(
            "app.services.agents.commercial_agent.generate_structured",
            new=AsyncMock(
                return_value=_mock_result({"sms_az": "Üzr isteyirik", "sms_en": "We apologize"})
            ),
        ),
    ):
        results = await AgentOrchestrationService(db_session).run_for_incident(incident.id)

    assert all(r.available for r in results)
    assert all(r.source.value == "live" for r in results)

    actions, total = await ActionRepository(db_session).list_paginated(50, 0)
    assert total == 3

    outputs = await AgentOutputRepository(db_session).list_for_incident(incident.id)
    assert len(outputs) == 3
    assert all(o.source.value == "live" for o in outputs)
    assert all(o.tokens == 42 for o in outputs)


async def test_failed_call_with_no_fallback_creates_no_action(db_session: AsyncSession):
    incident = await _seed_incident(db_session)

    with patch(
        "app.services.agents.network_agent.generate_structured",
        new=AsyncMock(side_effect=RuntimeError("API down")),
    ):
        from app.services.agents import network_agent

        result = await network_agent.run(db_session, incident.id)

    assert result.available is False
    assert result.output is None
    actions, total = await ActionRepository(db_session).list_paginated(50, 0)
    assert total == 0


async def test_failed_call_falls_back_to_most_recent_stored_output(db_session: AsyncSession):
    incident = await _seed_incident(db_session)

    await AgentOutputRepository(db_session).create(
        incident_id=incident.id,
        agent=ActionAgent.NETWORK,
        output={
            "summary": "Cached summary",
            "root_cause": "Cached cause",
            "runbook": ["Cached step"],
        },
        source="live",
        model="gemini-2.0-flash",
        tokens=10,
        latency_ms=500,
    )
    await db_session.commit()

    with patch(
        "app.services.agents.network_agent.generate_structured",
        new=AsyncMock(side_effect=RuntimeError("API down")),
    ):
        from app.services.agents import network_agent

        result = await network_agent.run(db_session, incident.id)

    assert result.available is True
    assert result.source.value == "fallback"
    assert result.output["summary"] == "Cached summary"


async def test_missing_api_key_falls_back_cleanly(db_session: AsyncSession):
    incident = await _seed_incident(db_session)
    from app.services.agents import commercial_agent

    # No GEMINI_API_KEY is set in the test environment, so the real client
    # call raises RuntimeError before ever reaching the network -- same
    # fallback path as any other failure, proven end to end without mocking.
    result = await commercial_agent.run(db_session, incident.id)
    assert result.available is False


async def test_auto_low_risk_autonomy_auto_executes_low_risk_action(db_session: AsyncSession):
    incident = await _seed_incident(db_session)
    db_session.add(Settings(autonomy_level=AutonomyLevel.AUTO_LOW_RISK))
    await db_session.commit()

    with patch(
        "app.services.agents.commercial_agent.generate_structured",
        new=AsyncMock(
            return_value=_mock_result({"sms_az": "Üzr isteyirik", "sms_en": "We apologize"})
        ),
    ):
        from app.services.agents import commercial_agent

        result = await commercial_agent.run(db_session, incident.id)
        assert result.available

        from app.services.agent_orchestration_service import AgentOrchestrationService as AOS

        await AOS(db_session).create_action_for_result(incident.id, result)

    actions, total = await ActionRepository(db_session).list_paginated(50, 0)
    assert total == 1
    assert actions[0].status == ActionStatus.EXECUTED
    assert actions[0].approved_at is not None


async def test_recommend_only_autonomy_keeps_low_risk_proposed(db_session: AsyncSession):
    # Default autonomy level (no Settings row yet) is recommend_only.
    incident = await _seed_incident(db_session)

    with patch(
        "app.services.agents.commercial_agent.generate_structured",
        new=AsyncMock(
            return_value=_mock_result({"sms_az": "Üzr isteyirik", "sms_en": "We apologize"})
        ),
    ):
        from app.services.agents import commercial_agent

        result = await commercial_agent.run(db_session, incident.id)
        from app.services.agent_orchestration_service import AgentOrchestrationService as AOS

        await AOS(db_session).create_action_for_result(incident.id, result)

    actions, total = await ActionRepository(db_session).list_paginated(50, 0)
    assert total == 1
    assert actions[0].status == ActionStatus.PROPOSED
