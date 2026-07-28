from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.integrations.ebay.rest import EbayRestClient

Clock = Callable[[], datetime]

MARKETPLACE_ID = "EBAY_IT"


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ConditionPolicy:
    condition_id: str
    condition_name: str
    condition_description_required: bool


@dataclass(frozen=True)
class CategoryMetadata:
    category_id: str
    allowed_conditions: tuple[ConditionPolicy, ...]
    regulatory_warnings: tuple[str, ...]
    retrieved_at: datetime
    expires_at: datetime

    def is_fresh(self, now: datetime) -> bool:
        return now < self.expires_at


@dataclass
class _CacheEntry:
    metadata: CategoryMetadata


class EbaySellMetadataClient:
    def __init__(
        self,
        rest_client: EbayRestClient,
        marketplace_id: str = MARKETPLACE_ID,
        clock: Clock = utcnow,
        cache_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self._rest_client = rest_client
        self._marketplace_id = marketplace_id
        self._clock = clock
        self._cache_ttl = cache_ttl
        self._cache: dict[str, _CacheEntry] = {}

    def get_category_metadata(self, category_id: str) -> CategoryMetadata:
        cached = self._cache.get(category_id)
        if cached is not None and cached.metadata.is_fresh(self._clock()):
            return cached.metadata

        payload = self._rest_client.get(
            f"/sell/metadata/v1/marketplace/{self._marketplace_id}/get_item_condition_policies",
            params={"category_id": category_id},
        )
        conditions: list[ConditionPolicy] = []
        regulatory_warnings: list[str] = []
        policies_raw = payload.get("itemConditionPolicies", [])
        policies = policies_raw if isinstance(policies_raw, list) else []
        for entry in policies:
            if not isinstance(entry, dict):
                continue
            item_conditions_raw = entry.get("itemConditions", [])
            item_conditions = item_conditions_raw if isinstance(item_conditions_raw, list) else []
            for condition in item_conditions:
                if not isinstance(condition, dict):
                    continue
                conditions.append(
                    ConditionPolicy(
                        condition_id=str(condition.get("conditionId", "")),
                        condition_name=str(condition.get("conditionDescription", "")),
                        condition_description_required=bool(
                            entry.get("itemConditionRequired", False)
                        ),
                    )
                )
            unknown_enum = entry.get("categoryTreeNodeAncestors")
            if unknown_enum is not None and not isinstance(unknown_enum, list):
                regulatory_warnings.append(
                    "eBay returned an unrecognized category metadata shape; treated as a warning."
                )

        now = self._clock()
        metadata = CategoryMetadata(
            category_id=category_id,
            allowed_conditions=tuple(conditions),
            regulatory_warnings=tuple(regulatory_warnings),
            retrieved_at=now,
            expires_at=now + self._cache_ttl,
        )
        self._cache[category_id] = _CacheEntry(metadata=metadata)
        return metadata
