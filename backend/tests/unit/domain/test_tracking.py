from datetime import UTC, datetime

from app.domain.tracking import (
    TrackingCheckpoint,
    TrackingDirection,
    TrackingRecord,
    TrackingStatus,
)


def test_tracking_record_starts_unknown_with_no_checkpoints():
    record = TrackingRecord(
        id="rec-1",
        direction=TrackingDirection.OUTBOUND,
        carrier="dhl",
        tracking_number="JD0001",
        label="Sold: lens",
        item_id="item-1",
        status=TrackingStatus.UNKNOWN,
        checkpoints=(),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert record.status is TrackingStatus.UNKNOWN
    assert record.checkpoints == ()
    assert record.last_refreshed_at is None


def test_inbound_record_has_no_item_link():
    record = TrackingRecord(
        id="rec-2",
        direction=TrackingDirection.INBOUND,
        carrier="ups",
        tracking_number="1Z999",
        label="Replacement battery",
        item_id=None,
        status=TrackingStatus.UNKNOWN,
        checkpoints=(),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert record.direction is TrackingDirection.INBOUND
    assert record.item_id is None


def test_checkpoint_holds_description_location_and_timestamp():
    checkpoint = TrackingCheckpoint(
        description="Departed facility",
        location="Milan, IT",
        provider_timestamp=datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert checkpoint.description == "Departed facility"
    assert checkpoint.location == "Milan, IT"
