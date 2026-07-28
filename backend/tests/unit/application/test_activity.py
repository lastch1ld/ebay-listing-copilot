from datetime import UTC, datetime

import pytest

from app.application.activity import ActivityEvent, ActivityService, RefreshTrigger
from app.persistence.database import create_session_factory
from app.persistence.models import Base

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class FakeSource:
    def __init__(self, name: str) -> None:
        self.name = name
        self.events: tuple[ActivityEvent, ...] = ()
        self.should_fail = False

    async def fetch_since(self, checkpoint):
        if self.should_fail:
            raise RuntimeError("provider outage")
        return self.events


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    return factory


@pytest.fixture
def offer_source() -> FakeSource:
    return FakeSource("offers")


@pytest.fixture
def order_source() -> FakeSource:
    return FakeSource("orders")


@pytest.fixture
def activity_service(session_factory, offer_source, order_source) -> ActivityService:
    return ActivityService(session_factory, sources=[offer_source, order_source], clock=lambda: NOW)


@pytest.mark.asyncio
async def test_same_offer_status_alerts_once(activity_service, offer_source):
    offer_source.events = (
        ActivityEvent(
            event_type="OFFER", provider_event_id="offer-1", provider_status="ACTIVE",
            provider_timestamp=NOW,
        ),
    )
    first = await activity_service.refresh(RefreshTrigger.STARTUP)
    second = await activity_service.refresh(RefreshTrigger.STARTUP)
    assert first.created == 1
    assert second.created == 0


@pytest.mark.asyncio
async def test_changed_refund_status_creates_new_alert(activity_service, order_source):
    order_source.events = (
        ActivityEvent(
            event_type="REFUND", provider_event_id="refund-1", provider_status="PENDING",
            provider_timestamp=NOW,
        ),
    )
    await activity_service.refresh(RefreshTrigger.STARTUP)

    order_source.events = (
        ActivityEvent(
            event_type="REFUND", provider_event_id="refund-1", provider_status="COMPLETED",
            provider_timestamp=NOW,
        ),
    )
    summary = await activity_service.refresh(RefreshTrigger.LISTING_MUTATION)
    assert summary.created == 1


@pytest.mark.asyncio
async def test_partial_source_failure_preserves_successful_events(
    activity_service, offer_source, order_source
):
    offer_source.should_fail = True
    order_source.events = (
        ActivityEvent(
            event_type="SALE", provider_event_id="order-1", provider_status="COMPLETED",
            provider_timestamp=NOW,
        ),
    )
    summary = await activity_service.refresh(RefreshTrigger.STARTUP)
    assert summary.created == 1
    assert summary.failed_sources == ("offers",)
