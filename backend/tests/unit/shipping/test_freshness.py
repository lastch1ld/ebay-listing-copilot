from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.common import Money
from app.domain.shipping import ShippingQuote, ShippingZone

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _quote(retrieved_at: datetime) -> ShippingQuote:
    return ShippingQuote(
        provider="fixed-rate",
        service_code="STANDARD",
        service_name="Standard",
        zone=ShippingZone.ITALY,
        amount=Money("EUR", Decimal("8.90")),
        tracking_included=True,
        insurance_included=False,
        transit_min_days=2,
        transit_max_days=4,
        is_estimate=False,
        source_urls=(),
        assumptions=(),
        retrieved_at=retrieved_at,
        expires_at=retrieved_at + timedelta(hours=24),
    )


def test_quote_is_fresh_within_24_hours():
    quote = _quote(retrieved_at=NOW - timedelta(hours=1))
    assert quote.is_fresh(NOW) is True


def test_quote_expires_after_24_hours():
    quote = _quote(retrieved_at=NOW - timedelta(hours=25))
    assert quote.is_fresh(NOW) is False


def test_quote_is_fresh_uses_explicit_expiry_not_retrieval_time():
    quote = _quote(retrieved_at=NOW - timedelta(hours=1))
    object.__setattr__(quote, "expires_at", NOW - timedelta(minutes=1))
    assert quote.is_fresh(NOW) is False
