import dataclasses
from decimal import Decimal

import pytest

from app.application.activity import ActivityService
from app.application.approval import ApprovalService
from app.application.listing_management import ListingManagementService, RevisionNotApprovedError
from app.domain.common import Money
from app.domain.draft import ListingDraft
from app.persistence.database import create_session_factory
from app.persistence.models import Base, ItemModel


def _draft(**overrides: object) -> ListingDraft:
    defaults: dict[str, object] = dict(
        sku="ITEM-1",
        marketplace_id="EBAY_IT",
        title="Vintage table lamp",
        category_id="20697",
        condition_id="3000",
        condition_description="Small scratch on the base",
        description="A vintage table lamp.",
        quantity=1,
        price=Money("EUR", Decimal("80.00")),
        payment_policy_id="pp-1",
        return_policy_id="rp-1",
        fulfillment_policy_id="fp-1",
        merchant_location_key="warehouse-1",
        packed_weight_kg="1.2",
        length_cm="20",
        width_cm="15",
        height_cm="10",
    )
    defaults.update(overrides)
    return ListingDraft(**defaults)  # type: ignore[arg-type]


class FakeEbayInventoryClient:
    def __init__(self) -> None:
        self.update_calls = 0
        self.withdraw_calls = 0

    def update_offer(self, offer_id: str, draft: ListingDraft) -> None:
        self.update_calls += 1

    def withdraw_offer(self, offer_id: str) -> None:
        self.withdraw_calls += 1


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as session:
        session.add(
            ItemModel(
                id="item-1",
                state="LIVE",
                description="Vintage lamp",
                defects="Small scratch on the base",
                target_price_currency="EUR",
                target_price_value="80.00",
            )
        )
        session.commit()
    return factory


@pytest.fixture
def ebay_client() -> FakeEbayInventoryClient:
    return FakeEbayInventoryClient()


@pytest.fixture
def activity_service(session_factory) -> ActivityService:
    return ActivityService(session_factory, sources=[])


@pytest.fixture
def service(session_factory, ebay_client, activity_service) -> ListingManagementService:
    return ListingManagementService(session_factory, ebay_client, activity_service)


@pytest.mark.asyncio
async def test_price_edit_cannot_update_offer_before_reapproval(
    service, session_factory, ebay_client
):
    approval_service = ApprovalService(session_factory)
    original_draft = _draft()
    approval = approval_service.approve("item-1", original_draft)

    revised_draft = dataclasses.replace(original_draft, price=Money("EUR", Decimal("90.00")))
    service.propose_revision("item-1", revised_draft)

    with pytest.raises(RevisionNotApprovedError):
        await service.apply_approved_revision("offer-1", approval, revised_draft)

    assert ebay_client.update_calls == 0


@pytest.mark.asyncio
async def test_reapproved_revision_is_applied(service, session_factory, ebay_client):
    approval_service = ApprovalService(session_factory)
    revised_draft = dataclasses.replace(_draft(), price=Money("EUR", Decimal("90.00")))
    new_approval = approval_service.approve("item-1", revised_draft)

    await service.apply_approved_revision("offer-1", new_approval, revised_draft)

    assert ebay_client.update_calls == 1


@pytest.mark.asyncio
async def test_two_withdrawal_requests_produce_at_most_one_provider_mutation(
    service, ebay_client
):
    await service.withdraw_approved_listing("offer-1", "summary-hash-1")
    await service.withdraw_approved_listing("offer-1", "summary-hash-1")

    assert ebay_client.withdraw_calls == 1
