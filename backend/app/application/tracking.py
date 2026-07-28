import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select

from app.domain.tracking import (
    TrackingCheckpoint,
    TrackingDirection,
    TrackingRecord,
    TrackingStatus,
)
from app.integrations.tracking.base import TrackingLookupError, TrackingProvider
from app.persistence.database import SessionFactory
from app.persistence.models import ItemModel, TrackingRecordModel

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


class TrackingRefreshTrigger(StrEnum):
    LOGIN = "LOGIN"
    MANUAL = "MANUAL"


class TrackingValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TrackingRefreshSummary:
    checked: int
    updated: int
    failed_record_ids: tuple[str, ...]


_LIVE_OR_LATER_STATES = {"LIVE", "AWAITING_APPROVAL", "APPROVED", "PUBLISHING"}


class TrackingService:
    def __init__(
        self,
        session_factory: SessionFactory,
        provider: TrackingProvider,
        clock: Clock = utcnow,
    ) -> None:
        self._session_factory = session_factory
        self._provider = provider
        self._clock = clock

    def add(
        self,
        direction: TrackingDirection,
        carrier: str,
        tracking_number: str,
        label: str,
        item_id: str | None = None,
    ) -> TrackingRecord:
        if direction is TrackingDirection.INBOUND and item_id is not None:
            raise TrackingValidationError("inbound tracking records cannot be linked to an item")
        if direction is TrackingDirection.OUTBOUND and item_id is not None:
            with self._session_factory() as session:
                item = session.get(ItemModel, item_id)
                if item is None or item.state not in _LIVE_OR_LATER_STATES:
                    raise TrackingValidationError(
                        "a linked item must already be published (LIVE or later)"
                    )

        with self._session_factory() as session:
            record = TrackingRecordModel(
                direction=direction.value,
                carrier=carrier,
                tracking_number=tracking_number,
                label=label,
                item_id=item_id,
                status=TrackingStatus.UNKNOWN.value,
                checkpoints_json="[]",
            )
            session.add(record)
            session.commit()
            return _to_domain(record)

    def list_all(self) -> tuple[TrackingRecord, ...]:
        with self._session_factory() as session:
            rows = session.scalars(select(TrackingRecordModel)).all()
            return tuple(_to_domain(row) for row in rows)

    async def refresh(
        self, trigger: TrackingRefreshTrigger, record_id: str | None = None
    ) -> TrackingRefreshSummary:
        if trigger is TrackingRefreshTrigger.MANUAL:
            if record_id is None:
                raise TrackingValidationError("record_id is required for a manual refresh")
            candidate_ids = [record_id]
        else:
            with self._session_factory() as session:
                candidate_ids = [
                    row.id
                    for row in session.scalars(
                        select(TrackingRecordModel).where(
                            TrackingRecordModel.status != TrackingStatus.DELIVERED.value
                        )
                    ).all()
                ]

        updated = 0
        failed: list[str] = []
        now = self._clock()
        for candidate_id in candidate_ids:
            with self._session_factory() as session:
                record = session.get(TrackingRecordModel, candidate_id)
                if record is None:
                    continue
                try:
                    snapshot = await self._provider.lookup(record.carrier, record.tracking_number)
                except TrackingLookupError:
                    failed.append(candidate_id)
                    continue
                record.status = snapshot.status.value
                record.checkpoints_json = json.dumps(
                    [
                        {
                            "description": checkpoint.description,
                            "location": checkpoint.location,
                            "provider_timestamp": checkpoint.provider_timestamp.isoformat(),
                        }
                        for checkpoint in snapshot.checkpoints
                    ]
                )
                record.last_refreshed_at = now
                session.commit()
                updated += 1

        return TrackingRefreshSummary(
            checked=len(candidate_ids), updated=updated, failed_record_ids=tuple(failed)
        )


def _to_domain(row: TrackingRecordModel) -> TrackingRecord:
    checkpoints = tuple(
        TrackingCheckpoint(
            description=entry["description"],
            location=entry["location"],
            provider_timestamp=datetime.fromisoformat(entry["provider_timestamp"]),
        )
        for entry in json.loads(row.checkpoints_json)
    )
    return TrackingRecord(
        id=row.id,
        direction=TrackingDirection(row.direction),
        carrier=row.carrier,
        tracking_number=row.tracking_number,
        label=row.label,
        item_id=row.item_id,
        status=TrackingStatus(row.status),
        checkpoints=checkpoints,
        created_at=row.created_at,
        last_refreshed_at=row.last_refreshed_at,
    )
