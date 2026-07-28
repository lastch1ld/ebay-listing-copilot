import httpx
import respx

from app.config import Environment
from app.integrations.ebay.metadata import EbaySellMetadataClient
from app.integrations.ebay.rest import EbayRestClient


def _client() -> EbaySellMetadataClient:
    rest_client = EbayRestClient(
        environment=Environment.SANDBOX, access_token_provider=lambda: "token-1"
    )
    return EbaySellMetadataClient(rest_client)


def test_get_category_metadata_parses_allowed_conditions() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(
            "https://api.sandbox.ebay.com/sell/metadata/v1/marketplace/EBAY_IT"
            "/get_item_condition_policies"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "itemConditionPolicies": [
                        {
                            "itemConditionRequired": True,
                            "itemConditions": [
                                {"conditionId": "3000", "conditionDescription": "Used"}
                            ],
                        }
                    ]
                },
            )
        )
        metadata = _client().get_category_metadata("123")

    assert len(metadata.allowed_conditions) == 1
    assert metadata.allowed_conditions[0].condition_name == "Used"
    assert metadata.allowed_conditions[0].condition_description_required is True


def test_unknown_enum_shape_becomes_a_warning_not_a_crash() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(
            "https://api.sandbox.ebay.com/sell/metadata/v1/marketplace/EBAY_IT"
            "/get_item_condition_policies"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "itemConditionPolicies": [
                        {
                            "itemConditionRequired": False,
                            "itemConditions": [],
                            "categoryTreeNodeAncestors": "unexpected-shape",
                        }
                    ]
                },
            )
        )
        metadata = _client().get_category_metadata("123")

    assert metadata.regulatory_warnings != ()
