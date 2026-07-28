from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TrackingDirection(StrEnum):
    OUTBOUND = "OUTBOUND"
    INBOUND = "INBOUND"


class TrackingStatus(StrEnum):
    INFO_RECEIVED = "INFO_RECEIVED"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    EXCEPTION = "EXCEPTION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TrackingCheckpoint:
    description: str
    location: str
    provider_timestamp: datetime


@dataclass(frozen=True)
class TrackingRecord:
    id: str
    direction: TrackingDirection
    carrier: str
    tracking_number: str
    label: str
    item_id: str | None
    status: TrackingStatus
    checkpoints: tuple[TrackingCheckpoint, ...]
    created_at: datetime
    last_refreshed_at: datetime | None = None
