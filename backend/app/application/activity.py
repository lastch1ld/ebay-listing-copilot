from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from app.persistence.database import SessionFactory
from app.persistence.models import ActivityEventModel
from app.persistence.repositories import ActivityRepository, CheckpointRepository

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


class RefreshTrigger(StrEnum):
    STARTUP = "STARTUP"
    LISTING_MUTATION = "LISTING_MUTATION"


@dataclass(frozen=True)
class ActivityEvent:
    event_type: str
    provider_event_id: str
    provider_status: str
    provider_timestamp: datetime
    listing_id: str | None = None
    order_id: str | None = None


class ActivitySource(Protocol):
    name: str

    async def fetch_since(self, checkpoint: datetime | None) -> tuple[ActivityEvent, ...]: ...


@dataclass(frozen=True)
class RefreshSummary:
    created: int
    failed_sources: tuple[str, ...]


class ActivityService:
    """Trigger-based, read-only refresh of offer/sale/refund activity.

    Never polls continuously and never invokes an offer-response or
    refund-write operation; it only normalizes provider events into
    deduplicated local notifications.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        sources: list[ActivitySource],
        clock: Clock = utcnow,
    ) -> None:
        self._activity_repository = ActivityRepository(session_factory)
        self._checkpoints = CheckpointRepository(session_factory)
        self._sources = sources
        self._clock = clock

    async def refresh(self, trigger: RefreshTrigger) -> RefreshSummary:
        created = 0
        failed_sources: list[str] = []
        now = self._clock()

        for source in self._sources:
            checkpoint = self._checkpoints.get(source.name)
            try:
                events = await source.fetch_since(checkpoint)
            except Exception:  # a single source's failure must not hide the rest
                failed_sources.append(source.name)
                continue

            for event in events:
                record = self._activity_repository.record_if_new(
                    ActivityEventModel(
                        event_type=event.event_type,
                        provider_event_id=event.provider_event_id,
                        listing_id=event.listing_id,
                        order_id=event.order_id,
                        provider_status=event.provider_status,
                        provider_timestamp=event.provider_timestamp,
                    )
                )
                if record is not None:
                    created += 1

            self._checkpoints.advance(source.name, now)

        return RefreshSummary(created=created, failed_sources=tuple(failed_sources))
