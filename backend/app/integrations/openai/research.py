import json
from decimal import Decimal
from typing import Any

import httpx

from app.application.research import ItemResearchRequest, ItemResearchResult
from app.domain.common import Money, Provenance, SourcedValue

RESPONSES_URL = "https://api.openai.com/v1/responses"

_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "identity": {
            "type": "object",
            "properties": {
                "value": {"type": ["string", "null"]},
                "provenance": {
                    "type": "string",
                    "enum": [p.value for p in Provenance],
                },
                "confidence": {"type": "number"},
                "sources": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["value", "provenance", "confidence", "sources"],
        },
        "comparable_prices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string"},
                    "value": {"type": "number"},
                },
                "required": ["currency", "value"],
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
        "questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["identity", "comparable_prices", "warnings", "questions"],
}


class InvalidResearchResultError(ValueError):
    pass


class ResearchNotConfiguredError(RuntimeError):
    pass


class UnconfiguredResearchClient:
    """Placeholder used until a real OPENAI_API_KEY and OPENAI_MODEL are set."""

    async def research_item(self, request: ItemResearchRequest) -> ItemResearchResult:
        raise ResearchNotConfiguredError(
            "OpenAI research is not configured; set OPENAI_API_KEY and OPENAI_MODEL"
        )


class OpenAIResearchClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not model:
            raise ValueError("OPENAI_MODEL must be configured; no hard-coded fallback is used")
        self._api_key = api_key
        self._model = model
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)

    async def research_item(self, request: ItemResearchRequest) -> ItemResearchResult:
        response = await self._http_client.post(
            RESPONSES_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=self._build_payload(request),
        )
        response.raise_for_status()
        return self._parse_result(response.json())

    def _build_payload(self, request: ItemResearchRequest) -> dict[str, Any]:
        return {
            "model": self._model,
            "input": [
                {
                    "role": "user",
                    "content": (
                        f"Description: {request.description}\n"
                        f"Known defects: {request.defects}\n"
                        f"Seller target price: {request.target_price.currency} "
                        f"{request.target_price.value}"
                    ),
                }
            ],
            "tools": [{"type": "web_search"}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "item_research_result",
                    "schema": _RESULT_SCHEMA,
                    "strict": True,
                }
            },
        }

    def _parse_result(self, payload: dict[str, Any]) -> ItemResearchResult:
        structured = json.loads(payload["output_text"])
        identity = self._parse_sourced_value(structured["identity"])
        comparable_prices = tuple(
            Money(entry["currency"], Decimal(str(entry["value"])))
            for entry in structured.get("comparable_prices", [])
        )
        return ItemResearchResult(
            identity=identity,
            comparable_prices=comparable_prices,
            warnings=tuple(structured.get("warnings", [])),
            questions=tuple(structured.get("questions", [])),
        )

    @staticmethod
    def _parse_sourced_value(data: dict[str, Any]) -> SourcedValue[str]:
        sources = tuple(data.get("sources", []))
        provenance = Provenance(data["provenance"])
        has_valid_https_source = sources and all(
            source.startswith("https://") for source in sources
        )
        if provenance is Provenance.SOURCE_VERIFIED and not has_valid_https_source:
            raise InvalidResearchResultError(
                "SOURCE_VERIFIED value must include at least one valid HTTPS source"
            )
        return SourcedValue(
            value=data.get("value"),
            provenance=provenance,
            confidence=Decimal(str(data["confidence"])),
            sources=sources,
        )
