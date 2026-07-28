from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.shipping import ShipmentRequest, ShippingQuote, ShippingZone
from app.integrations.shipping.base import ShippingProvider

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


NON_EU_CUSTOMS_WARNING = (
    "This destination is outside the EU customs union; duties, taxes, and customs "
    "paperwork may apply and are the buyer's responsibility unless stated otherwise."
)


@dataclass(frozen=True)
class ShippingRecommendation:
    zone: ShippingZone
    quotes: tuple[ShippingQuote, ...]
    selected: ShippingQuote | None
    publishable: bool
    customs_warning: str | None


class ShippingService:
    def __init__(self, providers: list[ShippingProvider], clock: Clock = utcnow) -> None:
        self._providers = providers
        self._clock = clock

    async def recommend(
        self, request: ShipmentRequest, zones: tuple[ShippingZone, ...]
    ) -> tuple[ShippingRecommendation, ...]:
        now = self._clock()
        recommendations = []
        for zone in zones:
            quotes = await self._collect_quotes(request, zone)
            ranked = self._rank(quotes)
            selected = self._select_publishable(ranked, now)
            recommendations.append(
                ShippingRecommendation(
                    zone=zone,
                    quotes=ranked,
                    selected=selected,
                    publishable=selected is not None,
                    customs_warning=(
                        NON_EU_CUSTOMS_WARNING if zone is ShippingZone.NON_EU_CONTINENTAL else None
                    ),
                )
            )
        return tuple(recommendations)

    async def _collect_quotes(
        self, request: ShipmentRequest, zone: ShippingZone
    ) -> tuple[ShippingQuote, ...]:
        collected: list[ShippingQuote] = []
        for provider in self._providers:
            collected.extend(await provider.quote(request, zone))
        return tuple(collected)

    @staticmethod
    def _rank(quotes: tuple[ShippingQuote, ...]) -> tuple[ShippingQuote, ...]:
        return tuple(sorted(quotes, key=lambda q: (q.amount.value, q.transit_max_days)))

    @staticmethod
    def _select_publishable(
        ranked_quotes: tuple[ShippingQuote, ...], now: datetime
    ) -> ShippingQuote | None:
        for quote in ranked_quotes:
            if not quote.is_estimate and quote.is_fresh(now):
                return quote
        return None
