from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.application.shipping import ShippingService
from app.domain.common import Money
from app.domain.shipping import ShipmentRequest, ShippingZone
from app.integrations.shipping.fixed_rates import FixedRateProvider
from app.integrations.shipping.research import (
    InvalidCarrierSourceError,
    RawCarrierQuote,
    ResearchShippingProvider,
)
from app.persistence.database import create_session_factory
from app.persistence.models import Base, ItemModel

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _request(destinations: tuple[str, ...] = ("DE",)) -> ShipmentRequest:
    return ShipmentRequest(
        origin_postcode="39100",
        packed_weight_kg="1.2",
        length_cm="20",
        width_cm="15",
        height_cm="10",
        declared_value=Money("EUR", Decimal("80.00")),
        restricted_items=(),
        destination_samples=destinations,
    )


class FakeLookup:
    def __init__(self, quotes: tuple[RawCarrierQuote, ...]) -> None:
        self._quotes = quotes

    async def find_quotes(self, request, zone):
        return self._quotes


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as session:
        session.add(
            ItemModel(
                id="item-1",
                state="INTAKE",
                description="Vintage lamp",
                defects="No known defects",
                target_price_currency="EUR",
                target_price_value="80.00",
            )
        )
        session.commit()
    return factory


@pytest.mark.asyncio
async def test_research_provider_labels_results_as_estimates():
    lookup = FakeLookup(
        (
            RawCarrierQuote(
                provider="poste-italiane",
                service_code="STD",
                service_name="Standard",
                amount=Money("EUR", Decimal("9.50")),
                transit_min_days=3,
                transit_max_days=6,
                tracking_included=True,
                insurance_included=False,
                source_url="https://example.invalid/rates",
                effective_date=date(2025, 12, 1),
            ),
        )
    )
    provider = ResearchShippingProvider(lookup, clock=lambda: NOW)
    quotes = await provider.quote(_request(), ShippingZone.EU_CONTINENTAL)

    assert len(quotes) == 1
    assert quotes[0].is_estimate is True
    assert quotes[0].source_urls == ("https://example.invalid/rates",)


@pytest.mark.asyncio
async def test_research_provider_rejects_non_https_source():
    lookup = FakeLookup(
        (
            RawCarrierQuote(
                provider="sketchy",
                service_code="STD",
                service_name="Standard",
                amount=Money("EUR", Decimal("5.00")),
                transit_min_days=1,
                transit_max_days=2,
                tracking_included=False,
                insurance_included=False,
                source_url="http://example.invalid/rates",
                effective_date=date(2025, 12, 1),
            ),
        )
    )
    provider = ResearchShippingProvider(lookup, clock=lambda: NOW)
    with pytest.raises(InvalidCarrierSourceError):
        await provider.quote(_request(), ShippingZone.EU_CONTINENTAL)


@pytest.mark.asyncio
async def test_research_provider_drops_stale_official_sources():
    lookup = FakeLookup(
        (
            RawCarrierQuote(
                provider="poste-italiane",
                service_code="STD",
                service_name="Standard",
                amount=Money("EUR", Decimal("9.50")),
                transit_min_days=3,
                transit_max_days=6,
                tracking_included=True,
                insurance_included=False,
                source_url="https://example.invalid/rates",
                effective_date=date(2020, 1, 1),
            ),
        )
    )
    provider = ResearchShippingProvider(lookup, clock=lambda: NOW)
    quotes = await provider.quote(_request(), ShippingZone.EU_CONTINENTAL)
    assert quotes == ()


@pytest.mark.asyncio
async def test_fixed_rate_provider_reads_seller_confirmed_rate(session_factory):
    fixed = FixedRateProvider(item_id="item-1", session_factory=session_factory, clock=lambda: NOW)
    fixed.confirm(
        zone=ShippingZone.EU_CONTINENTAL,
        provider="poste-italiane",
        service_code="STD",
        service_name="Standard",
        amount=Money("EUR", Decimal("9.50")),
        tracking_included=True,
        insurance_included=False,
        transit_min_days=3,
        transit_max_days=6,
    )
    quotes = await fixed.quote(_request(), ShippingZone.EU_CONTINENTAL)
    assert len(quotes) == 1
    assert quotes[0].is_estimate is False


@pytest.mark.asyncio
async def test_recommendation_is_publishable_only_with_a_fresh_fixed_rate(session_factory):
    research_lookup = FakeLookup(
        (
            RawCarrierQuote(
                provider="poste-italiane",
                service_code="STD",
                service_name="Standard",
                amount=Money("EUR", Decimal("9.50")),
                transit_min_days=3,
                transit_max_days=6,
                tracking_included=True,
                insurance_included=False,
                source_url="https://example.invalid/rates",
                effective_date=date(2025, 12, 1),
            ),
        )
    )
    research_provider = ResearchShippingProvider(research_lookup, clock=lambda: NOW)
    fixed_provider = FixedRateProvider(
        item_id="item-1", session_factory=session_factory, clock=lambda: NOW
    )

    service = ShippingService(providers=[research_provider, fixed_provider], clock=lambda: NOW)
    [only_estimates] = await service.recommend(_request(), (ShippingZone.EU_CONTINENTAL,))
    assert only_estimates.publishable is False
    assert only_estimates.selected is None

    fixed_provider.confirm(
        zone=ShippingZone.EU_CONTINENTAL,
        provider="poste-italiane",
        service_code="STD",
        service_name="Standard",
        amount=Money("EUR", Decimal("8.00")),
        tracking_included=True,
        insurance_included=False,
        transit_min_days=3,
        transit_max_days=6,
    )
    [with_fixed_rate] = await service.recommend(_request(), (ShippingZone.EU_CONTINENTAL,))
    assert with_fixed_rate.publishable is True
    assert with_fixed_rate.selected is not None
    assert with_fixed_rate.selected.is_estimate is False
    assert len(with_fixed_rate.quotes) == 2


@pytest.mark.asyncio
async def test_non_eu_zone_always_carries_a_customs_warning(session_factory):
    fixed_provider = FixedRateProvider(
        item_id="item-1", session_factory=session_factory, clock=lambda: NOW
    )
    service = ShippingService(providers=[fixed_provider], clock=lambda: NOW)
    [recommendation] = await service.recommend(
        _request(("CH",)), (ShippingZone.NON_EU_CONTINENTAL,)
    )
    assert recommendation.customs_warning is not None
    assert "customs" in recommendation.customs_warning.lower()


@pytest.mark.asyncio
async def test_stale_fixed_rate_is_not_publishable(session_factory):
    fixed_provider = FixedRateProvider(
        item_id="item-1", session_factory=session_factory, clock=lambda: NOW
    )
    fixed_provider.confirm(
        zone=ShippingZone.ITALY,
        provider="poste-italiane",
        service_code="STD",
        service_name="Standard",
        amount=Money("EUR", Decimal("6.00")),
        tracking_included=True,
        insurance_included=False,
        transit_min_days=1,
        transit_max_days=3,
        freshness_window=timedelta(hours=24),
    )
    later = lambda: NOW + timedelta(hours=25)  # noqa: E731
    service = ShippingService(providers=[fixed_provider], clock=later)
    [recommendation] = await service.recommend(_request(("IT",)), (ShippingZone.ITALY,))
    assert recommendation.publishable is False
