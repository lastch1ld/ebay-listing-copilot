import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.domain.common import Money, SourcedValue
from app.persistence.database import SessionFactory
from app.persistence.models import ItemModel, ResearchClaimModel


@dataclass(frozen=True)
class ItemResearchRequest:
    item_id: str
    description: str
    defects: str
    target_price: Money


@dataclass(frozen=True)
class ItemResearchResult:
    identity: SourcedValue[str]
    comparable_prices: tuple[Money, ...]
    warnings: tuple[str, ...]
    questions: tuple[str, ...]


class ResearchClient(Protocol):
    async def research_item(self, request: ItemResearchRequest) -> ItemResearchResult: ...


class ItemNotFoundError(ValueError):
    pass


class ResearchService:
    def __init__(self, client: ResearchClient, session_factory: SessionFactory) -> None:
        self._client = client
        self._session_factory = session_factory

    async def run(self, item_id: str) -> ItemResearchResult:
        request = self._build_request(item_id)
        result = await self._client.research_item(request)
        self._persist_claim(item_id, "identity", result.identity)
        return result

    def _build_request(self, item_id: str) -> ItemResearchRequest:
        with self._session_factory() as session:
            item = session.get(ItemModel, item_id)
            if item is None:
                raise ItemNotFoundError(f"item not found: {item_id}")
            return ItemResearchRequest(
                item_id=item_id,
                description=item.description,
                defects=item.defects,
                target_price=Money(item.target_price_currency, Decimal(item.target_price_value)),
            )

    def _persist_claim(self, item_id: str, field_name: str, value: SourcedValue[str]) -> None:
        with self._session_factory() as session:
            session.add(
                ResearchClaimModel(
                    item_id=item_id,
                    field_name=field_name,
                    value_json=json.dumps(value.value),
                    provenance=value.provenance.value,
                    confidence=str(value.confidence),
                    sources_json=json.dumps(list(value.sources)),
                )
            )
            session.commit()
