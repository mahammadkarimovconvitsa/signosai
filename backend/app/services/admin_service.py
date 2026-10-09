from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.agent_output import AgentOutput
from app.models.alarm import Alarm
from app.models.cell import Cell
from app.models.enums import OperationalStatus
from app.models.incident import Incident, IncidentAffectedSite, IncidentTimelineEvent
from app.models.link import Link
from app.models.site import Site
from app.models.user import User
from app.repositories.audit_repository import AuditRepository


class AdminService:
    """Resets operational/system-generated state only.

    Reference data (sites, cells, links, customers, contracts, runbooks,
    market items, business_config, users) is never touched — only its
    mutable `status` columns (site/link/cell) are reset to up, since those
    are flipped by incidents rather than owned by the data engineer.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditRepository(db)

    async def reset(self, actor: User) -> None:
        # Alarm references Incident via a FK, so it must go before Incident —
        # found live (not by the test suite, whose seed data had no alarms).
        await self.db.execute(delete(Alarm))
        await self.db.execute(delete(IncidentTimelineEvent))
        await self.db.execute(delete(IncidentAffectedSite))
        await self.db.execute(delete(Action))
        await self.db.execute(delete(AgentOutput))
        await self.db.execute(delete(Incident))

        await self.db.execute(update(Site).values(status=OperationalStatus.UP))
        await self.db.execute(update(Link).values(status=OperationalStatus.UP))
        await self.db.execute(update(Cell).values(status=OperationalStatus.UP))

        await self.audit.log(
            event_type="admin.reset",
            entity="system",
            actor_user_id=actor.id,
            actor_role=actor.role,
        )
        await self.db.commit()
