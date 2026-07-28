from datetime import datetime

from app.application.activity import ActivityEvent
from app.integrations.ebay.rest import EbayRestClient


class EbayTradingBestOffersSource:
    """Read-only buyer Best Offer / counter-offer activity via Trading GetBestOffers.

    Exposes only what a notification needs (listing, status, timestamp) and
    never a write method — accepting, countering, or declining an offer is
    out of scope for this adapter.
    """

    name = "ebay_best_offers"

    def __init__(self, rest_client: EbayRestClient) -> None:
        self._rest_client = rest_client

    async def fetch_since(self, checkpoint: datetime | None) -> tuple[ActivityEvent, ...]:
        payload = self._rest_client.get(
            "/trading/GetBestOffers",
            params={"ModTimeFrom": checkpoint.isoformat()} if checkpoint else None,
        )
        offers_raw = payload.get("BestOfferArray", [])
        offers = offers_raw if isinstance(offers_raw, list) else []

        events: list[ActivityEvent] = []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            offer_id = offer.get("BestOfferID")
            listing_id = offer.get("ItemID")
            status = offer.get("Status", "UNKNOWN")
            timestamp_raw = offer.get("OfferTime")
            if not isinstance(offer_id, str) or not isinstance(timestamp_raw, str):
                continue
            events.append(
                ActivityEvent(
                    event_type="OFFER",
                    provider_event_id=offer_id,
                    provider_status=str(status) if status is not None else "UNKNOWN",
                    provider_timestamp=datetime.fromisoformat(timestamp_raw),
                    listing_id=str(listing_id) if isinstance(listing_id, str) else None,
                )
            )
        return tuple(events)
