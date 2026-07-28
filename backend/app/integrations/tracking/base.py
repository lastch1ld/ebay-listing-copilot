from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.tracking import TrackingCheckpoint, TrackingStatus


class TrackingLookupError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrackingSnapshot:
    status: TrackingStatus
    checkpoints: tuple[TrackingCheckpoint, ...]
    last_update: datetime


class TrackingProvider(Protocol):
    async def lookup(self, carrier: str, tracking_number: str) -> TrackingSnapshot: ...
