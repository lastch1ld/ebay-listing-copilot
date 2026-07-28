"""Real eBay Sandbox smoke test.

Skipped unless RUN_EBAY_SANDBOX_E2E=1 and the required Sandbox credentials
are present. Never targets Production: every client below is constructed
with Environment.SANDBOX explicitly, and the CI workflow additionally runs
scripts/verify_no_production_calls.py against the recorded request log
before and after this test.
"""

import contextlib
import io
import os
from decimal import Decimal

import httpx
import pytest
from PIL import Image

from app.application.approval import ApprovalService
from app.application.publishing import PublishingService
from app.config import Environment
from app.domain.common import Money
from app.domain.draft import ListingDraft
from app.integrations.ebay.inventory import EbayInventoryClient
from app.integrations.ebay.media import EbayMediaClient
from app.integrations.ebay.oauth import EbayOAuth, EbayTokenStore
from app.integrations.ebay.rest import EbayRestClient
from app.persistence.database import create_session_factory
from app.persistence.models import Base
from app.security.secrets import SecretStore

pytestmark = pytest.mark.sandbox

REQUIRED_ENV_VARS = (
    "EBAY_SANDBOX_CLIENT_ID",
    "EBAY_SANDBOX_CLIENT_SECRET",
    "EBAY_SANDBOX_REFRESH_TOKEN",
)


def _skip_reason() -> str | None:
    if os.environ.get("RUN_EBAY_SANDBOX_E2E") != "1":
        return "set RUN_EBAY_SANDBOX_E2E=1 to run the real eBay Sandbox smoke test"
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        return f"missing required Sandbox credentials: {', '.join(missing)}"
    return None


def _fixture_draft() -> ListingDraft:
    return ListingDraft(
        sku=f"E2E-FIXTURE-{os.getpid()}",
        marketplace_id="EBAY_IT",
        title="[TEST FIXTURE] Do not buy - automated Sandbox smoke test",
        category_id="20697",
        condition_id="1000",
        condition_description="Fictional fixture item created by an automated test.",
        description="Fictional fixture item created by an automated test. Not a real listing.",
        quantity=1,
        price=Money("EUR", Decimal("1.00")),
        payment_policy_id=os.environ.get("EBAY_SANDBOX_PAYMENT_POLICY_ID", ""),
        return_policy_id=os.environ.get("EBAY_SANDBOX_RETURN_POLICY_ID", ""),
        fulfillment_policy_id=os.environ.get("EBAY_SANDBOX_FULFILLMENT_POLICY_ID", ""),
        merchant_location_key=os.environ.get("EBAY_SANDBOX_MERCHANT_LOCATION_KEY", ""),
        packed_weight_kg="0.2",
        length_cm="10",
        width_cm="10",
        height_cm="5",
    )


def _fixture_jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color=(120, 120, 120)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.skipif(_skip_reason() is not None, reason=_skip_reason() or "")
def _recording_http_client() -> httpx.Client:
    """Logs every request URL so the production-call guard has real data to check."""
    log_path = os.environ.get("RECORDED_REQUESTS_FILE")

    def record(request: httpx.Request) -> None:
        if log_path:
            with open(log_path, "a", encoding="utf-8") as handle:
                handle.write(f"{request.url}\n")

    return httpx.Client(timeout=30.0, event_hooks={"request": [record]})


def test_sandbox_publish_and_withdraw_one_fictional_listing() -> None:
    token_store = EbayTokenStore(SecretStore(service="ebay-listing-copilot-sandbox-e2e"))
    token_store.set("sandbox", os.environ["EBAY_SANDBOX_REFRESH_TOKEN"])

    shared_http_client = _recording_http_client()

    oauth = EbayOAuth(
        client_id=os.environ["EBAY_SANDBOX_CLIENT_ID"],
        client_secret=os.environ["EBAY_SANDBOX_CLIENT_SECRET"],
        redirect_uri="http://127.0.0.1:8000/api/auth/ebay/callback",
        environment=Environment.SANDBOX,
        scopes=(
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account",
        ),
        token_store=token_store,
        http_client=shared_http_client,
    )

    def access_token_provider() -> str:
        return oauth.refresh().access_token

    rest_client = EbayRestClient(
        environment=Environment.SANDBOX,
        access_token_provider=access_token_provider,
        http_client=shared_http_client,
    )
    inventory_client = EbayInventoryClient(rest_client)
    media_client = EbayMediaClient(rest_client)

    session_factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    approval_service = ApprovalService(session_factory)
    publishing_service = PublishingService(session_factory, inventory_client)

    draft = _fixture_draft()
    image = media_client.upload("fixture.jpg", "image/jpeg", _fixture_jpeg_bytes())
    draft_ref = inventory_client.create_draft(draft, image_urls=(image.url,))

    approval = approval_service.approve("e2e-fixture-item", draft)
    assert approval.payload_hash

    listing_ref = None
    try:
        listing_ref = publishing_service.publish(
            offer_id=draft_ref.offer_id, draft_hash=approval.payload_hash
        )
        assert listing_ref.listing_id
    finally:
        # Best-effort Sandbox cleanup; a stray fixture offer is not a Production risk.
        with contextlib.suppress(httpx.HTTPError):
            inventory_client.withdraw_offer(draft_ref.offer_id)
