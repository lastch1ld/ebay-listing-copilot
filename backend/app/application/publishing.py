import json
from dataclasses import asdict, dataclass

from app.integrations.ebay.inventory import EbayInventoryClient, OfferPublishAmbiguousError
from app.persistence.database import SessionFactory
from app.persistence.repositories import OperationRepository


@dataclass(frozen=True)
class ListingRef:
    offer_id: str
    listing_id: str
    listing_url: str


class PublishingService:
    def __init__(
        self,
        session_factory: SessionFactory,
        ebay_client: EbayInventoryClient,
        marketplace_domain: str = "www.ebay.it",
    ) -> None:
        self._operations = OperationRepository(session_factory)
        self._ebay_client = ebay_client
        self._marketplace_domain = marketplace_domain

    def publish(self, offer_id: str, draft_hash: str) -> ListingRef:
        operation = self._operations.begin(f"publish:{offer_id}:{draft_hash}")
        if operation.status == "COMPLETED" and operation.result_json is not None:
            return ListingRef(**json.loads(operation.result_json))

        try:
            listing_id = self._ebay_client.publish_offer(offer_id)
        except OfferPublishAmbiguousError:
            offer_status = self._ebay_client.get_offer(offer_id)
            if offer_status.listing_id is None:
                raise
            listing_id = offer_status.listing_id

        listing_ref = ListingRef(
            offer_id=offer_id,
            listing_id=listing_id,
            listing_url=f"https://{self._marketplace_domain}/itm/{listing_id}",
        )
        self._operations.complete(operation.id, json.dumps(asdict(listing_ref)))
        return listing_ref
