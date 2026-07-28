from decimal import Decimal

import httpx
import pytest
import respx

from app.config import Environment
from app.domain.common import Money
from app.domain.draft import ListingDraft
from app.integrations.ebay.inventory import (
    EbayInventoryClient,
    ProductionAcknowledgementRequiredError,
)
from app.integrations.ebay.rest import EbayRestClient


def _draft() -> ListingDraft:
    return ListingDraft(
        sku="ITEM-1",
        marketplace_id="EBAY_IT",
        title="Vintage table lamp",
        category_id="20697",
        condition_id="3000",
        condition_description="Small scratch on left side of the base",
        description="A vintage table lamp in used condition.",
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


def _client() -> EbayInventoryClient:
    rest_client = EbayRestClient(
        environment=Environment.SANDBOX, access_token_provider=lambda: "token-1"
    )
    return EbayInventoryClient(rest_client)


def test_create_draft_creates_inventory_item_and_offer_with_fee_estimate() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.put("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/ITEM-1").mock(
            return_value=httpx.Response(204)
        )
        mock.post("https://api.sandbox.ebay.com/sell/inventory/v1/offer").mock(
            return_value=httpx.Response(201, json={"offerId": "offer-1", "warnings": []})
        )
        mock.post(
            "https://api.sandbox.ebay.com/sell/inventory/v1/offer/get_listing_fees"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "feeSummaries": [
                        {"fees": [{"amount": {"value": "3.20", "currency": "EUR"}}]}
                    ]
                },
            )
        )
        draft_ref = _client().create_draft(
            _draft(), image_urls=("https://i.ebayimg.invalid/img-1.jpg",)
        )

    assert draft_ref.offer_id == "offer-1"
    assert draft_ref.fee_estimate is not None
    assert draft_ref.fee_estimate.amount == Money("EUR", Decimal("3.20"))


def test_create_draft_tolerates_missing_fee_estimate() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.put("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/ITEM-1").mock(
            return_value=httpx.Response(204)
        )
        mock.post("https://api.sandbox.ebay.com/sell/inventory/v1/offer").mock(
            return_value=httpx.Response(201, json={"offerId": "offer-1", "warnings": []})
        )
        mock.post(
            "https://api.sandbox.ebay.com/sell/inventory/v1/offer/get_listing_fees"
        ).mock(return_value=httpx.Response(503))
        draft_ref = _client().create_draft(_draft(), image_urls=())

    assert draft_ref.fee_estimate is None


def test_production_draft_requires_seller_hub_acknowledgement() -> None:
    with pytest.raises(ProductionAcknowledgementRequiredError):
        _client().create_draft(_draft(), image_urls=(), is_production=True)


def test_production_draft_proceeds_when_acknowledged() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.put("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/ITEM-1").mock(
            return_value=httpx.Response(204)
        )
        mock.post("https://api.sandbox.ebay.com/sell/inventory/v1/offer").mock(
            return_value=httpx.Response(201, json={"offerId": "offer-1", "warnings": []})
        )
        mock.post(
            "https://api.sandbox.ebay.com/sell/inventory/v1/offer/get_listing_fees"
        ).mock(return_value=httpx.Response(503))
        draft_ref = _client().create_draft(
            _draft(), image_urls=(), is_production=True, seller_hub_acknowledged=True
        )

    assert draft_ref.offer_id == "offer-1"
