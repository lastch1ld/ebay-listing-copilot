import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Stores timestamps as naive UTC and always returns UTC-aware datetimes.

    SQLite's DATETIME storage does not retain timezone offsets, so timezone
    awareness has to be enforced at the application boundary instead.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime is not allowed; provide a timezone-aware value")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        result: datetime = value.replace(tzinfo=UTC)
        return result


class Base(DeclarativeBase):
    type_annotation_map = {  # noqa: RUF012
        datetime: UTCDateTime,
    }


class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    state: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    defects: Mapped[str] = mapped_column(nullable=False)
    target_price_currency: Mapped[str] = mapped_column(nullable=False)
    target_price_value: Mapped[str] = mapped_column(nullable=False)
    ship_from_country: Mapped[str | None] = mapped_column(nullable=True)
    ship_from_postcode: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow, onupdate=_utcnow)


class PhotoModel(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    sha256: Mapped[str] = mapped_column(nullable=False)
    filename: Mapped[str] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)


class ResearchClaimModel(Base):
    __tablename__ = "research_claims"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(nullable=False)
    value_json: Mapped[str] = mapped_column(nullable=False)
    provenance: Mapped[str] = mapped_column(nullable=False)
    confidence: Mapped[str] = mapped_column(nullable=False)
    sources_json: Mapped[str] = mapped_column(nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)


class DraftVersionModel(Base):
    __tablename__ = "draft_versions"
    __table_args__ = (UniqueConstraint("item_id", "version_number"),)

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    payload_json: Mapped[str] = mapped_column(nullable=False)
    payload_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)


class ApprovalModel(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    draft_version_id: Mapped[str] = mapped_column(
        ForeignKey("draft_versions.id"), nullable=False, unique=True
    )
    payload_hash: Mapped[str] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(nullable=False)
    approved_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)


class OperationModel(Base):
    __tablename__ = "operations"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    operation_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
    result_json: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow, onupdate=_utcnow)


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    job_type: Mapped[str] = mapped_column(nullable=False)
    input_json: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    lease_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    result_ref: Mapped[str | None] = mapped_column(nullable=True)
    error_json: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow, onupdate=_utcnow)


class ShippingQuoteModel(Base):
    __tablename__ = "shipping_quotes"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    provider: Mapped[str] = mapped_column(nullable=False)
    service: Mapped[str] = mapped_column(nullable=False)
    zone: Mapped[str] = mapped_column(nullable=False)
    amount_currency: Mapped[str] = mapped_column(nullable=False)
    amount_value: Mapped[str] = mapped_column(nullable=False)
    transit_estimate: Mapped[str] = mapped_column(nullable=False)
    tracking_supported: Mapped[bool] = mapped_column(nullable=False, default=False)
    insurance_supported: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_estimate: Mapped[bool] = mapped_column(nullable=False, default=True)
    retrieved_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class ActivityEventModel(Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        UniqueConstraint("event_type", "provider_event_id", "provider_status"),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(nullable=False)
    provider_event_id: Mapped[str] = mapped_column(nullable=False)
    listing_id: Mapped[str | None] = mapped_column(nullable=True)
    order_id: Mapped[str | None] = mapped_column(nullable=True)
    provider_status: Mapped[str] = mapped_column(nullable=False)
    provider_timestamp: Mapped[datetime] = mapped_column(nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    read_state: Mapped[str] = mapped_column(nullable=False, default="UNREAD")


class CheckpointModel(Base):
    __tablename__ = "checkpoints"

    source_name: Mapped[str] = mapped_column(primary_key=True)
    last_processed_at: Mapped[datetime] = mapped_column(nullable=False)
    cursor: Mapped[str | None] = mapped_column(nullable=True)


class TrackingRecordModel(Base):
    __tablename__ = "tracking_records"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    direction: Mapped[str] = mapped_column(nullable=False)
    carrier: Mapped[str] = mapped_column(nullable=False)
    tracking_number: Mapped[str] = mapped_column(nullable=False)
    label: Mapped[str] = mapped_column(nullable=False)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("items.id"), nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="UNKNOWN")
    checkpoints_json: Mapped[str] = mapped_column(nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(nullable=True)
