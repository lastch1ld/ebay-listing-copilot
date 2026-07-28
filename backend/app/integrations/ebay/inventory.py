from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.domain.common import Money
from app.domain.draft import ListingDraft
from app.integrations.ebay.rest import EbayRestClient


class ProductionAcknowledgementRequiredError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeeEstimate:
    amount: Money
    is_available: bool


@dataclass(frozen=True)
class EbayDraftRef:
    sku: str
    offer_id: str
    warnings: tuple[str, ...]
    fee_estimate: FeeEstimate | None


@dataclass(frozen=True)
class EbayOfferStatus:
    offer_id: str
    listing_id: str | None
    status: str


class OfferPublishAmbiguousError(RuntimeError):
    pass


_SELLER_HUB_ACKNOWLEDGEMENT = (
    "Listings created through the Inventory API must be revised through this "
    "application/API and cannot currently be edited in Seller Hub."
)


class EbayInventoryClient:
    def __init__(self, rest_client: EbayRestClient) -> None:
        self._rest_client = rest_client

    def create_draft(
        self,
        draft: ListingDraft,
        image_urls: tuple[str, ...],
        is_production: bool = False,
        seller_hub_acknowledged: bool = False,
    ) -> EbayDraftRef:
        if is_production and not seller_hub_acknowledged:
            raise ProductionAcknowledgementRequiredError(_SELLER_HUB_ACKNOWLEDGEMENT)

        self._create_or_replace_inventory_item(draft, image_urls)
        offer_id, warnings = self._create_offer(draft)
        fee_estimate = self._get_listing_fees(offer_id)
        return EbayDraftRef(
            sku=draft.sku,
            offer_id=offer_id,
            warnings=warnings,
            fee_estimate=fee_estimate,
        )

    def publish_offer(self, offer_id: str) -> str:
        try:
            payload = self._rest_client.post(f"/sell/inventory/v1/offer/{offer_id}/publish", {})
        except httpx.TimeoutException as error:
            raise OfferPublishAmbiguousError(
                f"publish for offer {offer_id} timed out; reconcile with get_offer before retry"
            ) from error
        listing_id = payload.get("listingId")
        if not isinstance(listing_id, str):
            raise OfferPublishAmbiguousError(
                f"publish for offer {offer_id} did not return a listingId; "
                "reconcile with get_offer before retry"
            )
        return listing_id

    def update_offer(self, offer_id: str, draft: ListingDraft) -> None:
        self._rest_client.put(
            f"/sell/inventory/v1/offer/{offer_id}",
            {
                "sku": draft.sku,
                "marketplaceId": draft.marketplace_id,
                "format": "FIXED_PRICE",
                "categoryId": draft.category_id,
                "listingDescription": draft.description,
                "availableQuantity": draft.quantity,
                "pricingSummary": {
                    "price": {
                        "value": str(draft.price.value),
                        "currency": draft.price.currency,
                    }
                },
                "listingPolicies": {
                    "paymentPolicyId": draft.payment_policy_id,
                    "returnPolicyId": draft.return_policy_id,
                    "fulfillmentPolicyId": draft.fulfillment_policy_id,
                },
                "merchantLocationKey": draft.merchant_location_key,
            },
        )

    def withdraw_offer(self, offer_id: str) -> None:
        self._rest_client.post(f"/sell/inventory/v1/offer/{offer_id}/withdraw", {})

    def get_offer(self, offer_id: str) -> EbayOfferStatus:
        payload = self._rest_client.get(f"/sell/inventory/v1/offer/{offer_id}")
        listing = payload.get("listing")
        listing_id = None
        if isinstance(listing, dict):
            raw_listing_id = listing.get("listingId")
            listing_id = raw_listing_id if isinstance(raw_listing_id, str) else None
        status = payload.get("status")
        return EbayOfferStatus(
            offer_id=offer_id,
            listing_id=listing_id,
            status=str(status) if status is not None else "UNKNOWN",
        )

    def _create_or_replace_inventory_item(
        self, draft: ListingDraft, image_urls: tuple[str, ...]
    ) -> None:
        self._rest_client.put(
            f"/sell/inventory/v1/inventory_item/{draft.sku}",
            {
                "condition": draft.condition_id,
                "conditionDescription": draft.condition_description,
                "product": {
                    "title": draft.title,
                    "description": draft.description,
                    "imageUrls": list(image_urls),
                },
                "availability": {
                    "shipToLocationAvailability": {"quantity": draft.quantity},
                },
                "packageWeightAndSize": {
                    "weight": {"value": draft.packed_weight_kg, "unit": "KILOGRAM"},
                    "dimensions": {
                        "length": draft.length_cm,
                        "width": draft.width_cm,
                        "height": draft.height_cm,
                        "unit": "CENTIMETER",
                    },
                },
            },
        )

    def _create_offer(self, draft: ListingDraft) -> tuple[str, tuple[str, ...]]:
        payload = self._rest_client.post(
            "/sell/inventory/v1/offer",
            {
                "sku": draft.sku,
                "marketplaceId": draft.marketplace_id,
                "format": "FIXED_PRICE",
                "categoryId": draft.category_id,
                "listingDescription": draft.description,
                "availableQuantity": draft.quantity,
                "pricingSummary": {
                    "price": {
                        "value": str(draft.price.value),
                        "currency": draft.price.currency,
                    }
                },
                "listingPolicies": {
                    "paymentPolicyId": draft.payment_policy_id,
                    "returnPolicyId": draft.return_policy_id,
                    "fulfillmentPolicyId": draft.fulfillment_policy_id,
                },
                "merchantLocationKey": draft.merchant_location_key,
            },
        )
        offer_id = payload.get("offerId")
        if not isinstance(offer_id, str):
            raise RuntimeError("eBay did not return an offerId for the created offer")
        warnings_raw = payload.get("warnings", [])
        warnings = tuple(
            str(warning.get("message", warning))
            for warning in (warnings_raw if isinstance(warnings_raw, list) else [])
        )
        return offer_id, warnings

    def _get_listing_fees(self, offer_id: str) -> FeeEstimate | None:
        try:
            payload = self._rest_client.post(
                "/sell/inventory/v1/offer/get_listing_fees",
                {"offers": [{"offerId": offer_id}]},
            )
        except httpx.HTTPError:
            return None

        fees_raw = payload.get("feeSummaries", [])
        fees = fees_raw if isinstance(fees_raw, list) else []
        for summary in fees:
            if not isinstance(summary, dict):
                continue
            fee_details_raw = summary.get("fees", [])
            fee_details = fee_details_raw if isinstance(fee_details_raw, list) else []
            for fee in fee_details:
                if not isinstance(fee, dict):
                    continue
                amount = fee.get("amount", {})
                if isinstance(amount, dict) and "value" in amount and "currency" in amount:
                    return FeeEstimate(
                        amount=Money(str(amount["currency"]), _to_decimal(amount["value"])),
                        is_available=True,
                    )
        return None


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))
