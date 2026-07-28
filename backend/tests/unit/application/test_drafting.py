from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.application.drafting import (
    DraftComposer,
    DraftValidationError,
    ItemForDrafting,
)
from app.application.shipping import ShippingRecommendation
from app.domain.common import Money
from app.domain.shipping import ShippingQuote, ShippingZone

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _fixed_quote(zone: ShippingZone) -> ShippingQuote:
    return ShippingQuote(
        provider="poste-italiane",
        service_code="STD",
        service_name="Standard",
        zone=zone,
        amount=Money("EUR", Decimal("8.00")),
        tracking_included=True,
        insurance_included=False,
        transit_min_days=2,
        transit_max_days=5,
        is_estimate=False,
        source_urls=(),
        assumptions=("seller-confirmed rate",),
        retrieved_at=NOW,
        expires_at=NOW + timedelta(hours=24),
    )


def _publishable_recommendation(zone: ShippingZone) -> ShippingRecommendation:
    quote = _fixed_quote(zone)
    return ShippingRecommendation(
        zone=zone, quotes=(quote,), selected=quote, publishable=True, customs_warning=None
    )


def _researched_item(**overrides: object) -> ItemForDrafting:
    defaults: dict[str, object] = dict(
        item_id="item-1",
        description="Vintage table lamp",
        defects="Small scratch on left side of the base",
        target_price=Money("EUR", Decimal("80.00")),
        category_id="20697",
        condition_id="3000",
        sku="ITEM-1",
        quantity=1,
        payment_policy_id="pp-1",
        return_policy_id="rp-1",
        fulfillment_policy_id="fp-1",
        merchant_location_key="warehouse-1",
        packed_weight_kg="1.2",
        length_cm="20",
        width_cm="15",
        height_cm="10",
        restricted_items=(),
        dangerous_goods_acknowledged=False,
        shipping_recommendations=(_publishable_recommendation(ShippingZone.ITALY),),
    )
    defaults.update(overrides)
    return ItemForDrafting(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def composer() -> DraftComposer:
    return DraftComposer()


@pytest.fixture
def researched_item() -> ItemForDrafting:
    return _researched_item()


def test_composer_preserves_user_defects_and_target_price(composer, researched_item):
    draft = composer.compose(researched_item)
    assert "scratch on left side" in draft.condition_description.lower()
    assert draft.price == Money("EUR", Decimal("80.00"))


def test_composer_blocks_missing_category(composer):
    item = _researched_item(category_id="")
    with pytest.raises(DraftValidationError, match="category"):
        composer.compose(item)


def test_composer_blocks_unconfirmed_dimensions(composer):
    item = _researched_item(packed_weight_kg="")
    with pytest.raises(DraftValidationError, match="weight"):
        composer.compose(item)


def test_composer_blocks_stale_or_unpublishable_shipping(composer):
    quote = _fixed_quote(ShippingZone.ITALY)
    unpublishable = ShippingRecommendation(
        zone=ShippingZone.ITALY, quotes=(quote,), selected=None, publishable=False,
        customs_warning=None,
    )
    item = _researched_item(shipping_recommendations=(unpublishable,))
    with pytest.raises(DraftValidationError, match="shipping"):
        composer.compose(item)


def test_composer_blocks_unacknowledged_dangerous_goods(composer):
    item = _researched_item(
        restricted_items=("lithium battery",), dangerous_goods_acknowledged=False
    )
    with pytest.raises(DraftValidationError, match="dangerous"):
        composer.compose(item)


def test_composer_allows_acknowledged_dangerous_goods(composer):
    item = _researched_item(
        restricted_items=("lithium battery",), dangerous_goods_acknowledged=True
    )
    draft = composer.compose(item)
    assert draft.sku == "ITEM-1"


def test_composer_blocks_omitted_defects_disguised_as_no_known_defects(composer):
    item = _researched_item(defects="")
    with pytest.raises(DraftValidationError, match="defect"):
        composer.compose(item)
