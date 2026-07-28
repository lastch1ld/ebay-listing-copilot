from datetime import datetime

from app.application.activity import ActivityEvent
from app.integrations.ebay.rest import EbayRestClient


class EbayFulfillmentOrdersSource:
    """Read-only completed-sale and refund-status activity via Fulfillment getOrders.

    Only listing/order identifiers, status, and timestamps are surfaced;
    buyer addresses, emails, and payment details are never included, and no
    write (refund-issuing) method is exposed.
    """

    name = "ebay_orders"

    def __init__(self, rest_client: EbayRestClient) -> None:
        self._rest_client = rest_client

    async def fetch_since(self, checkpoint: datetime | None) -> tuple[ActivityEvent, ...]:
        payload = self._rest_client.get(
            "/sell/fulfillment/v1/order",
            params={"filter": f"lastmodifieddate:[{checkpoint.isoformat()}..]"}
            if checkpoint
            else None,
        )
        orders_raw = payload.get("orders", [])
        orders = orders_raw if isinstance(orders_raw, list) else []

        events: list[ActivityEvent] = []
        for order in orders:
            if not isinstance(order, dict):
                continue
            order_id = order.get("orderId")
            last_modified = order.get("lastModifiedDate")
            if not isinstance(order_id, str) or not isinstance(last_modified, str):
                continue
            timestamp = datetime.fromisoformat(last_modified)

            order_status = order.get("orderFulfillmentStatus", "UNKNOWN")
            events.append(
                ActivityEvent(
                    event_type="SALE",
                    provider_event_id=order_id,
                    provider_status=str(order_status),
                    provider_timestamp=timestamp,
                    order_id=order_id,
                )
            )

            payment_summary = order.get("paymentSummary", {})
            refunds_raw = (
                payment_summary.get("refunds", []) if isinstance(payment_summary, dict) else []
            )
            refunds = refunds_raw if isinstance(refunds_raw, list) else []
            for refund in refunds:
                if not isinstance(refund, dict):
                    continue
                refund_id = refund.get("refundId")
                refund_status = refund.get("refundStatus", "UNKNOWN")
                if not isinstance(refund_id, str):
                    continue
                events.append(
                    ActivityEvent(
                        event_type="REFUND",
                        provider_event_id=refund_id,
                        provider_status=str(refund_status),
                        provider_timestamp=timestamp,
                        order_id=order_id,
                    )
                )
        return tuple(events)
