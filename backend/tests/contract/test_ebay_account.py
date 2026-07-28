import httpx
import respx

from app.config import Environment
from app.integrations.ebay.account import EbayAccountClient
from app.integrations.ebay.rest import EbayRestClient


def _client() -> EbayAccountClient:
    rest_client = EbayRestClient(
        environment=Environment.SANDBOX, access_token_provider=lambda: "token-1"
    )
    return EbayAccountClient(rest_client)


def test_readiness_reports_missing_steps_when_nothing_is_configured() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/payment_policy").mock(
            return_value=httpx.Response(200, json={"paymentPolicies": []})
        )
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/return_policy").mock(
            return_value=httpx.Response(200, json={"returnPolicies": []})
        )
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/fulfillment_policy").mock(
            return_value=httpx.Response(200, json={"fulfillmentPolicies": []})
        )
        mock.get("https://api.sandbox.ebay.com/sell/inventory/v1/location").mock(
            return_value=httpx.Response(200, json={"locations": []})
        )
        readiness = _client().readiness()

    assert readiness.is_ready is False
    assert len(readiness.missing_steps) == 4


def test_readiness_is_ready_when_everything_is_configured() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/payment_policy").mock(
            return_value=httpx.Response(200, json={"paymentPolicies": [{"name": "Standard"}]})
        )
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/return_policy").mock(
            return_value=httpx.Response(200, json={"returnPolicies": [{"name": "Standard"}]})
        )
        mock.get("https://api.sandbox.ebay.com/sell/account/v1/fulfillment_policy").mock(
            return_value=httpx.Response(200, json={"fulfillmentPolicies": [{"name": "Standard"}]})
        )
        mock.get("https://api.sandbox.ebay.com/sell/inventory/v1/location").mock(
            return_value=httpx.Response(200, json={"locations": [{"merchantLocationKey": "1"}]})
        )
        readiness = _client().readiness()

    assert readiness.is_ready is True
    assert readiness.missing_steps == ()
