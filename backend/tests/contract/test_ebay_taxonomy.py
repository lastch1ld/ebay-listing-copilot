from datetime import UTC, datetime

import httpx
import respx

from app.config import Environment
from app.integrations.ebay.rest import EbayRestClient
from app.integrations.ebay.taxonomy import EbayTaxonomyClient


def _client(clock=lambda: datetime(2026, 1, 1, tzinfo=UTC)) -> EbayTaxonomyClient:
    rest_client = EbayRestClient(
        environment=Environment.SANDBOX, access_token_provider=lambda: "token-1"
    )
    return EbayTaxonomyClient(rest_client, clock=clock)


def test_suggest_categories_parses_response() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(
            "https://api.sandbox.ebay.com/commerce/taxonomy/v1/category_tree/3"
            "/get_category_suggestions"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "categorySuggestions": [
                        {"category": {"categoryId": "123", "categoryName": "Table Lamps"}}
                    ]
                },
            )
        )
        suggestions = _client().suggest_categories("vintage lamp")

    assert len(suggestions) == 1
    assert suggestions[0].category_id == "123"
    assert suggestions[0].category_name == "Table Lamps"


def test_suggest_categories_uses_cache_and_avoids_second_call() -> None:
    client = _client()
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(
            "https://api.sandbox.ebay.com/commerce/taxonomy/v1/category_tree/3"
            "/get_category_suggestions"
        ).mock(return_value=httpx.Response(200, json={"categorySuggestions": []}))
        client.suggest_categories("vintage lamp")
        client.suggest_categories("vintage lamp")

    assert route.call_count == 1


def test_get_required_aspects_marks_required_fields() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(
            "https://api.sandbox.ebay.com/commerce/taxonomy/v1/category_tree/3"
            "/get_item_aspects_for_category"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "aspects": [
                        {
                            "localizedAspectName": "Brand",
                            "aspectConstraint": {"aspectRequired": True},
                        }
                    ]
                },
            )
        )
        aspects = _client().get_required_aspects("123")

    assert aspects[0].name == "Brand"
    assert aspects[0].required is True
