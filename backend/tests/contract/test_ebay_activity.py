import httpx
import pytest
import respx

from app.config import Environment
from app.integrations.ebay.fulfillment import EbayFulfillmentOrdersSource
from app.integrations.ebay.rest import EbayRestClient
from app.integrations.ebay.trading import EbayTradingBestOffersSource


def _rest_client() -> EbayRestClient:
    return EbayRestClient(environment=Environment.SANDBOX, access_token_provider=lambda: "token-1")


@pytest.mark.asyncio
async def test_best_offers_source_parses_events_and_tolerates_unknown_fields():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.sandbox.ebay.com/trading/GetBestOffers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "BestOfferArray": [
                        {
                            "BestOfferID": "offer-1",
                            "ItemID": "listing-1",
                            "Status": "ACTIVE",
                            "OfferTime": "2026-01-01T00:00:00+00:00",
                            "SomeFutureField": "unexpected-shape",
                        }
                    ]
                },
            )
        )
        source = EbayTradingBestOffersSource(_rest_client())
        events = await source.fetch_since(None)

    assert len(events) == 1
    assert events[0].provider_event_id == "offer-1"
    assert events[0].provider_status == "ACTIVE"


@pytest.mark.asyncio
async def test_orders_source_parses_sale_and_refund_without_buyer_data():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.sandbox.ebay.com/sell/fulfillment/v1/order").mock(
            return_value=httpx.Response(
                200,
                json={
                    "orders": [
                        {
                            "orderId": "order-1",
                            "lastModifiedDate": "2026-01-01T00:00:00+00:00",
                            "orderFulfillmentStatus": "FULFILLED",
                            "paymentSummary": {
                                "refunds": [
                                    {"refundId": "refund-1", "refundStatus": "PENDING"}
                                ]
                            },
                            "buyer": {"email": "buyer@example.invalid"},
                        }
                    ]
                },
            )
        )
        source = EbayFulfillmentOrdersSource(_rest_client())
        events = await source.fetch_since(None)

    event_types = {event.event_type for event in events}
    assert event_types == {"SALE", "REFUND"}
    for event in events:
        assert "buyer" not in vars(event)
