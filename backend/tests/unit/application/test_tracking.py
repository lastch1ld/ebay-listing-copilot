from datetime import UTC, datetime

import pytest

from app.application.tracking import (
    TrackingRefreshTrigger,
    TrackingService,
    TrackingValidationError,
)
from app.domain.tracking import TrackingCheckpoint, TrackingDirection, TrackingStatus
from app.integrations.tracking.base import TrackingLookupError, TrackingSnapshot
from app.persistence.database import create_session_factory
from app.persistence.models import Base, ItemModel

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def tracking_snapshot(status: str) -> TrackingSnapshot:
    return TrackingSnapshot(
        status=TrackingStatus(status),
        checkpoints=(TrackingCheckpoint("Update", "Milan, IT", NOW),),
        last_update=NOW,
    )


class FakeProvider:
    def __init__(self) -> None:
        self.snapshots: dict[str, TrackingSnapshot] = {}

    async def lookup(self, carrier: str, tracking_number: str) -> TrackingSnapshot:
        key = f"{carrier}:{tracking_number}"
        if key not in self.snapshots:
            raise TrackingLookupError(f"no fixture snapshot for {key}")
        return self.snapshots[key]


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as session:
        session.add(
            ItemModel(
                id="item-1",
                state="LIVE",
                description="Vintage lens",
                defects="No known defects",
                target_price_currency="EUR",
                target_price_value="120.00",
            )
        )
        session.commit()
    return factory


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def tracking_service(session_factory, provider) -> TrackingService:
    return TrackingService(session_factory, provider, clock=lambda: NOW)


@pytest.mark.asyncio
async def test_delivered_record_excluded_from_login_refresh(tracking_service, provider):
    tracking_service.add(
        direction=TrackingDirection.OUTBOUND,
        carrier="dhl",
        tracking_number="JD0001",
        label="Sold: lens",
        item_id="item-1",
    )
    provider.snapshots["dhl:JD0001"] = tracking_snapshot("DELIVERED")
    await tracking_service.refresh(TrackingRefreshTrigger.LOGIN)

    provider.snapshots["dhl:JD0001"] = tracking_snapshot("EXCEPTION")
    summary = await tracking_service.refresh(TrackingRefreshTrigger.LOGIN)
    assert summary.checked == 0


@pytest.mark.asyncio
async def test_manual_refresh_still_reaches_delivered_record(tracking_service, provider):
    record = tracking_service.add(
        direction=TrackingDirection.OUTBOUND,
        carrier="dhl",
        tracking_number="JD0001",
        label="Sold: lens",
        item_id="item-1",
    )
    provider.snapshots["dhl:JD0001"] = tracking_snapshot("DELIVERED")
    await tracking_service.refresh(TrackingRefreshTrigger.LOGIN)

    summary = await tracking_service.refresh(TrackingRefreshTrigger.MANUAL, record_id=record.id)
    assert summary.checked == 1


def test_inbound_record_requires_no_item_link(tracking_service):
    record = tracking_service.add(
        direction=TrackingDirection.INBOUND,
        carrier="ups",
        tracking_number="1Z999",
        label="Replacement battery",
    )
    assert record.item_id is None
    assert record.direction is TrackingDirection.INBOUND


def test_inbound_record_rejects_an_item_link(tracking_service):
    with pytest.raises(TrackingValidationError):
        tracking_service.add(
            direction=TrackingDirection.INBOUND,
            carrier="ups",
            tracking_number="1Z999",
            label="Replacement battery",
            item_id="item-1",
        )


def test_outbound_record_rejects_item_not_yet_live(tracking_service, session_factory):
    with session_factory() as session:
        session.add(
            ItemModel(
                id="item-2",
                state="INTAKE",
                description="Not yet live",
                defects="No known defects",
                target_price_currency="EUR",
                target_price_value="20.00",
            )
        )
        session.commit()

    with pytest.raises(TrackingValidationError):
        tracking_service.add(
            direction=TrackingDirection.OUTBOUND,
            carrier="dhl",
            tracking_number="JD0002",
            label="Sold: widget",
            item_id="item-2",
        )


@pytest.mark.asyncio
async def test_failed_lookup_leaves_last_known_good_status(tracking_service, provider):
    record = tracking_service.add(
        direction=TrackingDirection.OUTBOUND,
        carrier="dhl",
        tracking_number="JD0003",
        label="Sold: item",
        item_id="item-1",
    )
    provider.snapshots["dhl:JD0003"] = tracking_snapshot("IN_TRANSIT")
    await tracking_service.refresh(TrackingRefreshTrigger.MANUAL, record_id=record.id)

    del provider.snapshots["dhl:JD0003"]
    summary = await tracking_service.refresh(TrackingRefreshTrigger.MANUAL, record_id=record.id)
    assert summary.failed_record_ids == (record.id,)

    refreshed = tracking_service.list_all()
    matching = next(r for r in refreshed if r.id == record.id)
    assert matching.status is TrackingStatus.IN_TRANSIT
