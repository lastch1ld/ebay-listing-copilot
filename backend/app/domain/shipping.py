from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.common import Money

DEFAULT_FRESHNESS_WINDOW = timedelta(hours=24)


class ShippingZone(StrEnum):
    ITALY = "ITALY"
    EU_CONTINENTAL = "EU_CONTINENTAL"
    NON_EU_CONTINENTAL = "NON_EU_CONTINENTAL"


class UnsupportedDestinationError(ValueError):
    pass


_ITALY = {"IT"}
_EU_CONTINENTAL = {
    "AT",
    "BE",
    "BG",
    "CZ",
    "DE",
    "DK",
    "ES",
    "FI",
    "FR",
    "HR",
    "HU",
    "LU",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
}
_NON_EU_CONTINENTAL = {"CH", "NO"}


def classify_country(country_code: str) -> ShippingZone:
    code = country_code.upper()
    if code in _ITALY:
        return ShippingZone.ITALY
    if code in _EU_CONTINENTAL:
        return ShippingZone.EU_CONTINENTAL
    if code in _NON_EU_CONTINENTAL:
        return ShippingZone.NON_EU_CONTINENTAL
    raise UnsupportedDestinationError(f"unsupported destination for the first release: {code}")


@dataclass(frozen=True)
class ShippingQuote:
    provider: str
    service_code: str
    service_name: str
    zone: ShippingZone
    amount: Money
    tracking_included: bool
    insurance_included: bool
    transit_min_days: int
    transit_max_days: int
    is_estimate: bool
    source_urls: tuple[str, ...]
    assumptions: tuple[str, ...]
    retrieved_at: datetime
    expires_at: datetime

    def is_fresh(self, now: datetime) -> bool:
        return now < self.expires_at


@dataclass(frozen=True)
class ShipmentRequest:
    origin_postcode: str
    packed_weight_kg: str
    length_cm: str
    width_cm: str
    height_cm: str
    declared_value: Money
    restricted_items: tuple[str, ...]
    destination_samples: tuple[str, ...]
