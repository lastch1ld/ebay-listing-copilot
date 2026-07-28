from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.integrations.ebay.rest import EbayRestClient

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class CategorySuggestion:
    category_id: str
    category_name: str


@dataclass(frozen=True)
class AspectRequirement:
    name: str
    required: bool


@dataclass
class _CacheEntry:
    value: object
    expires_at: datetime


def _get_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key, [])
    return value if isinstance(value, list) else []


class EbayTaxonomyClient:
    def __init__(
        self,
        rest_client: EbayRestClient,
        category_tree_id: str = "3", # eBay Italy's default category-tree ID
        clock: Clock = utcnow,
        cache_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self._rest_client = rest_client
        self._category_tree_id = category_tree_id
        self._clock = clock
        self._cache_ttl = cache_ttl
        self._cache: dict[str, _CacheEntry] = {}

    def suggest_categories(self, query: str) -> tuple[CategorySuggestion, ...]:
        cache_key = f"suggest:{query}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        payload = self._rest_client.get(
            f"/commerce/taxonomy/v1/category_tree/{self._category_tree_id}"
            "/get_category_suggestions",
            params={"q": query},
        )
        suggestions = tuple(
            CategorySuggestion(
                category_id=str(entry["category"]["categoryId"]),
                category_name=str(entry["category"]["categoryName"]),
            )
            for entry in _get_list(payload, "categorySuggestions")
            if isinstance(entry, dict)
        )
        self._set_cached(cache_key, suggestions)
        return suggestions

    def get_required_aspects(self, category_id: str) -> tuple[AspectRequirement, ...]:
        cache_key = f"aspects:{category_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        payload = self._rest_client.get(
            f"/commerce/taxonomy/v1/category_tree/{self._category_tree_id}"
            "/get_item_aspects_for_category",
            params={"category_id": category_id},
        )
        aspects: list[AspectRequirement] = []
        for entry in _get_list(payload, "aspects"):
            if not isinstance(entry, dict):
                continue
            constraint = entry.get("aspectConstraint", {})
            aspects.append(
                AspectRequirement(
                    name=str(entry.get("localizedAspectName", "")),
                    required=bool(constraint.get("aspectRequired", False)),
                )
            )
        result = tuple(aspects)
        self._set_cached(cache_key, result)
        return result

    def _get_cached(self, key: str) -> object | None:
        entry = self._cache.get(key)
        if entry is None or entry.expires_at <= self._clock():
            return None
        return entry.value

    def _set_cached(self, key: str, value: object) -> None:
        self._cache[key] = _CacheEntry(value=value, expires_at=self._clock() + self._cache_ttl)
