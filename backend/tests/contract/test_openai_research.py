import json
from decimal import Decimal

import httpx
import pytest
import respx

from app.application.research import ItemResearchRequest
from app.domain.common import Money, Provenance
from app.integrations.openai.research import (
    RESPONSES_URL,
    InvalidResearchResultError,
    OpenAIResearchClient,
)


def _request() -> ItemResearchRequest:
    return ItemResearchRequest(
        item_id="item-1",
        description="Vintage lamp",
        defects="No known defects",
        target_price=Money("EUR", Decimal("80.00")),
    )


@pytest.mark.asyncio
async def test_research_client_parses_structured_response():
    structured = {
        "identity": {
            "value": "Model X",
            "provenance": Provenance.SOURCE_VERIFIED.value,
            "confidence": 0.9,
            "sources": ["https://example.invalid/model-x"],
        },
        "comparable_prices": [{"currency": "EUR", "value": 75.0}],
        "warnings": [],
        "questions": [],
    }

    with respx.mock(assert_all_called=True) as mock:
        mock.post(RESPONSES_URL).mock(
            return_value=httpx.Response(200, json={"output_text": json.dumps(structured)})
        )
        async with httpx.AsyncClient() as http_client:
            client = OpenAIResearchClient(
                api_key="sk-test", model="gpt-test", http_client=http_client
            )
            result = await client.research_item(_request())

    assert result.identity.value == "Model X"
    assert result.identity.provenance is Provenance.SOURCE_VERIFIED
    assert result.comparable_prices == (Money("EUR", Decimal("75.0")),)


@pytest.mark.asyncio
async def test_research_client_rejects_source_verified_without_https_source():
    structured = {
        "identity": {
            "value": "Model X",
            "provenance": Provenance.SOURCE_VERIFIED.value,
            "confidence": 0.9,
            "sources": [],
        },
        "comparable_prices": [],
        "warnings": [],
        "questions": [],
    }

    with respx.mock(assert_all_called=True) as mock:
        mock.post(RESPONSES_URL).mock(
            return_value=httpx.Response(200, json={"output_text": json.dumps(structured)})
        )
        async with httpx.AsyncClient() as http_client:
            client = OpenAIResearchClient(
                api_key="sk-test", model="gpt-test", http_client=http_client
            )
            with pytest.raises(InvalidResearchResultError):
                await client.research_item(_request())


def test_research_client_requires_configured_model():
    with pytest.raises(ValueError, match="OPENAI_MODEL"):
        OpenAIResearchClient(api_key="sk-test", model="")
