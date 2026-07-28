from typing import Protocol

from app.domain.shipping import ShipmentRequest, ShippingQuote, ShippingZone


class ShippingProvider(Protocol):
    async def quote(
        self, request: ShipmentRequest, zone: ShippingZone
    ) -> tuple[ShippingQuote, ...]: ...
