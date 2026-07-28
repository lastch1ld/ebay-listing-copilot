from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.domain.common import Money
from app.domain.shipping import (
    DEFAULT_FRESHNESS_WINDOW,
    ShipmentRequest,
    ShippingQuote,
    ShippingZone,
)
from app.persistence.database import SessionFactory
from app.persistence.models import ShippingQuoteModel

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


class FixedRateProvider:
    """Reads seller-confirmed, publishable shipping rates persisted locally."""

    def __init__(
        self,
        item_id: str,
        session_factory: SessionFactory,
        clock: Clock = utcnow,
    ) -> None:
        self._item_id = item_id
        self._session_factory = session_factory
        self._clock = clock

    def confirm(
        self,
        zone: ShippingZone,
        provider: str,
        service_code: str,
        service_name: str,
        amount: Money,
        tracking_included: bool,
        insurance_included: bool,
        transit_min_days: int,
        transit_max_days: int,
        freshness_window: timedelta = DEFAULT_FRESHNESS_WINDOW,
    ) -> None:
        now = self._clock()
        with self._session_factory() as session:
            session.add(
                ShippingQuoteModel(
                    item_id=self._item_id,
                    provider=provider,
                    service=f"{service_code}:{service_name}",
                    zone=zone.value,
                    amount_currency=amount.currency,
                    amount_value=str(amount.value),
                    transit_estimate=f"{transit_min_days}-{transit_max_days}",
                    tracking_supported=tracking_included,
                    insurance_supported=insurance_included,
                    is_estimate=False,
                    retrieved_at=now,
                    expires_at=now + freshness_window,
                )
            )
            session.commit()

    async def quote(
        self, request: ShipmentRequest, zone: ShippingZone
    ) -> tuple[ShippingQuote, ...]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(ShippingQuoteModel).where(
                    ShippingQuoteModel.item_id == self._item_id,
                    ShippingQuoteModel.zone == zone.value,
                    ShippingQuoteModel.is_estimate.is_(False),
                )
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    @staticmethod
    def _to_domain(row: ShippingQuoteModel) -> ShippingQuote:
        service_code, _, service_name = row.service.partition(":")
        transit_min, _, transit_max = row.transit_estimate.partition("-")
        return ShippingQuote(
            provider=row.provider,
            service_code=service_code,
            service_name=service_name,
            zone=ShippingZone(row.zone),
            amount=Money(row.amount_currency, Decimal(row.amount_value)),
            tracking_included=row.tracking_supported,
            insurance_included=row.insurance_supported,
            transit_min_days=int(transit_min),
            transit_max_days=int(transit_max),
            is_estimate=False,
            source_urls=(),
            assumptions=("seller-confirmed rate",),
            retrieved_at=row.retrieved_at,
            expires_at=row.expires_at,
        )
