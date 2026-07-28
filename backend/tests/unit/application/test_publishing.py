import pytest

from app.application.publishing import PublishingService
from app.integrations.ebay.inventory import EbayOfferStatus, OfferPublishAmbiguousError
from app.persistence.database import create_session_factory
from app.persistence.models import Base


class FakeEbayInventoryClient:
    def __init__(self) -> None:
        self.publish_calls = 0
        self.next_listing_id: str | None = "listing-1"
        self.ambiguous = False
        self.offer_status = EbayOfferStatus(
            offer_id="offer-1", listing_id="listing-1", status="PUBLISHED"
        )

    def publish_offer(self, offer_id: str) -> str:
        self.publish_calls += 1
        if self.ambiguous:
            raise OfferPublishAmbiguousError("ambiguous response")
        assert self.next_listing_id is not None
        return self.next_listing_id

    def get_offer(self, offer_id: str) -> EbayOfferStatus:
        return self.offer_status


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    return factory


def test_publish_returns_listing_ref(session_factory):
    ebay_client = FakeEbayInventoryClient()
    service = PublishingService(session_factory, ebay_client)

    listing_ref = service.publish(offer_id="offer-1", draft_hash="hash-1")

    assert listing_ref.listing_id == "listing-1"
    assert listing_ref.listing_url.endswith("/itm/listing-1")


def test_two_publish_requests_produce_one_provider_mutation(session_factory):
    ebay_client = FakeEbayInventoryClient()
    service = PublishingService(session_factory, ebay_client)

    first = service.publish(offer_id="offer-1", draft_hash="hash-1")
    second = service.publish(offer_id="offer-1", draft_hash="hash-1")

    assert ebay_client.publish_calls == 1
    assert first == second


def test_ambiguous_publish_reconciles_via_get_offer(session_factory):
    ebay_client = FakeEbayInventoryClient()
    ebay_client.ambiguous = True
    service = PublishingService(session_factory, ebay_client)

    listing_ref = service.publish(offer_id="offer-1", draft_hash="hash-1")

    assert listing_ref.listing_id == "listing-1"


def test_ambiguous_publish_without_resolvable_listing_reraises(session_factory):
    ebay_client = FakeEbayInventoryClient()
    ebay_client.ambiguous = True
    ebay_client.offer_status = EbayOfferStatus(
        offer_id="offer-1", listing_id=None, status="UNKNOWN"
    )
    service = PublishingService(session_factory, ebay_client)

    with pytest.raises(OfferPublishAmbiguousError):
        service.publish(offer_id="offer-1", draft_hash="hash-1")


def test_different_draft_hash_creates_a_new_publish_operation(session_factory):
    ebay_client = FakeEbayInventoryClient()
    service = PublishingService(session_factory, ebay_client)

    service.publish(offer_id="offer-1", draft_hash="hash-1")
    service.publish(offer_id="offer-1", draft_hash="hash-2")

    assert ebay_client.publish_calls == 2
