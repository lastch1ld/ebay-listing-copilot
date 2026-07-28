import dataclasses
from decimal import Decimal

import pytest

from app.application.approval import ApprovalService, payload_hash
from app.domain.common import Money
from app.domain.draft import ListingDraft
from app.persistence.database import create_session_factory
from app.persistence.models import Base, ItemModel


def _draft() -> ListingDraft:
    return ListingDraft(
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


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as session:
        session.add(
            ItemModel(
                id="item-1",
                state="AWAITING_APPROVAL",
                description="Vintage lamp",
                defects="Small scratch on the base",
                target_price_currency="EUR",
                target_price_value="80.00",
            )
        )
        session.commit()
    return factory


@pytest.fixture
def approval_service(session_factory) -> ApprovalService:
    return ApprovalService(session_factory)


def test_material_change_invalidates_approval(approval_service):
    draft = _draft()
    approval = approval_service.approve("item-1", draft)

    changed = dataclasses.replace(draft, price=Money("EUR", Decimal("81.00")))
    assert approval_service.matches(approval, changed) is False


def test_unchanged_draft_still_matches_approval(approval_service):
    draft = _draft()
    approval = approval_service.approve("item-1", draft)
    assert approval_service.matches(approval, draft) is True


def test_key_order_does_not_change_hash():
    assert payload_hash({"a": 1, "b": 2}) == payload_hash({"b": 2, "a": 1})


def test_approve_creates_incrementing_draft_versions(approval_service):
    draft = _draft()
    first = approval_service.approve("item-1", draft)
    changed = dataclasses.replace(draft, price=Money("EUR", Decimal("85.00")))
    second = approval_service.approve("item-1", changed)
    assert first.draft_version_id != second.draft_version_id
    assert first.payload_hash != second.payload_hash
