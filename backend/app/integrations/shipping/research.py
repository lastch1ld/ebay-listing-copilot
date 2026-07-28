from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from app.domain.common import Money
from app.domain.shipping import (
    DEFAULT_FRESHNESS_WINDOW,
    ShipmentRequest,
    ShippingQuote,
    ShippingZone,
)

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class RawCarrierQuote:
    provider: str
    service_code: str
    service_name: str
    amount: Money
    transit_min_days: int
    transit_max_days: int
    tracking_included: bool
    insurance_included: bool
    source_url: str
    effective_date: date


class ShippingSourceLookup(Protocol):
    async def find_quotes(
        self, request: ShipmentRequest, zone: ShippingZone
    ) -> tuple[RawCarrierQuote, ...]: ...


class InvalidCarrierSourceError(ValueError):
    pass


class ResearchShippingProvider:
    """Turns official carrier/aggregator research into labeled shipping estimates.

    Every quote must cite an HTTPS source with an effective date; results are
    always marked as estimates and never treated as purchasable rates.
    """

    def __init__(
        self,
        lookup: ShippingSourceLookup,
        clock: Clock = utcnow,
        freshness_window: timedelta = DEFAULT_FRESHNESS_WINDOW,
        max_source_age: timedelta = timedelta(days=180),
    ) -> None:
        self._lookup = lookup
        self._clock = clock
        self._freshness_window = freshness_window
        self._max_source_age = max_source_age

    async def quote(
        self, request: ShipmentRequest, zone: ShippingZone
    ) -> tuple[ShippingQuote, ...]:
        raw_quotes = await self._lookup.find_quotes(request, zone)
        now = self._clock()
        quotes: list[ShippingQuote] = []
        for raw in raw_quotes:
            if not raw.source_url.startswith("https://"):
                raise InvalidCarrierSourceError(
                    f"{raw.provider} quote is missing a valid HTTPS source"
                )
            source_age = now.date() - raw.effective_date
            if source_age > self._max_source_age:
                continue
            quotes.append(
                ShippingQuote(
                    provider=raw.provider,
                    service_code=raw.service_code,
                    service_name=raw.service_name,
                    zone=zone,
                    amount=raw.amount,
                    tracking_included=raw.tracking_included,
                    insurance_included=raw.insurance_included,
                    transit_min_days=raw.transit_min_days,
                    transit_max_days=raw.transit_max_days,
                    is_estimate=True,
                    source_urls=(raw.source_url,),
                    assumptions=(f"official source effective {raw.effective_date.isoformat()}",),
                    retrieved_at=now,
                    expires_at=now + self._freshness_window,
                )
            )
        return tuple(quotes)
