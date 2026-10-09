from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OperationalStatus
from app.models.incident import Incident
from app.models.link import Link
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.network_repository import LinkRepository, SiteRepository


class CorrelationService:
    """Collapses a batch of unprocessed alarms into a single incident.

    Algorithm: group alarm-reporting sites by their upstream link, pick the link
    shared by the most sites (skipping protected links — those never explain an
    outage by design), then treat every site behind that link as affected,
    whether or not it happened to report an alarm yet. Reuses an existing OPEN
    incident for the same root-cause link instead of duplicating it.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.alarms = AlarmRepository(db)
        self.incidents = IncidentRepository(db)
        self.sites = SiteRepository(db)
        self.links = LinkRepository(db)

    async def correlate(self) -> Incident | None:
        unprocessed = await self.alarms.list_unprocessed()
        if not unprocessed:
            return None

        alarm_site_ids = {a.site_id for a in unprocessed}
        alarm_sites = await self.sites.get_many(list(alarm_site_ids))

        link_votes: Counter[UUID] = Counter(
            site.uplink_link_id for site in alarm_sites if site.uplink_link_id is not None
        )
        if not link_votes:
            return None

        root_link = await self._pick_root_link(link_votes)
        if root_link is None:
            return None

        affected_sites = await self.sites.list_by_uplink_link(root_link.id)
        affected_site_ids = {s.id for s in affected_sites}

        await self.links.set_status(root_link, OperationalStatus.DOWN)
        for site in affected_sites:
            await self.sites.set_status(site, OperationalStatus.DOWN)

        relevant_alarms = [a for a in unprocessed if a.site_id in affected_site_ids]
        started_at = min((a.timestamp for a in relevant_alarms), default=datetime.now(UTC))

        incident = await self.incidents.get_open_by_root_cause_link(root_link.id)
        is_new = incident is None
        if incident is None:
            incident = await self.incidents.create(
                root_cause_link_id=root_link.id,
                root_cause_summary=await self._summary(root_link),
                started_at=started_at,
            )

        for site_id in affected_site_ids:
            await self.incidents.add_affected_site_if_missing(incident.id, site_id)

        await self.alarms.mark_processed([a.id for a in relevant_alarms], incident.id)
        await self._record_timeline(
            incident, is_new, started_at, relevant_alarms, affected_site_ids
        )

        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def _pick_root_link(self, link_votes: Counter) -> Link | None:
        for link_id, _count in link_votes.most_common():
            link = await self.links.get_by_id(link_id)
            if link is not None and not link.is_protected:
                return link
        return None

    async def _summary(self, link: Link) -> str:
        from_site = await self.sites.get_by_id(link.from_site_id)
        to_site = await self.sites.get_by_id(link.to_site_id)
        from_name = from_site.name if from_site else str(link.from_site_id)
        to_name = to_site.name if to_site else str(link.to_site_id)
        return f"Fiber link cut between {from_name} and {to_name}"

    async def _record_timeline(
        self,
        incident: Incident,
        is_new: bool,
        started_at: datetime,
        relevant_alarms: list,
        affected_site_ids: set,
    ) -> None:
        now = datetime.now(UTC)
        if is_new:
            await self.incidents.add_timeline_event(
                incident.id,
                started_at,
                "alarms_received",
                f"{len(relevant_alarms)} alarms received from {len(affected_site_ids)} sites",
            )
            await self.incidents.add_timeline_event(
                incident.id,
                now,
                "correlated",
                f"Root cause: link {incident.root_cause_link_id} down",
            )
        else:
            await self.incidents.add_timeline_event(
                incident.id,
                now,
                "alarms_received",
                f"{len(relevant_alarms)} additional alarms received",
            )
