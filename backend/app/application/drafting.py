from dataclasses import dataclass, field

from app.application.shipping import ShippingRecommendation
from app.domain.common import Money
from app.domain.draft import ListingDraft

MARKETPLACE_ID = "EBAY_IT"
MAX_TITLE_LENGTH = 80


class DraftValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ItemForDrafting:
    item_id: str
    description: str
    defects: str
    target_price: Money
    category_id: str
    condition_id: str
    sku: str
    payment_policy_id: str
    return_policy_id: str
    fulfillment_policy_id: str
    merchant_location_key: str
    packed_weight_kg: str
    length_cm: str
    width_cm: str
    height_cm: str
    shipping_recommendations: tuple[ShippingRecommendation, ...]
    quantity: int = 1
    restricted_items: tuple[str, ...] = field(default_factory=tuple)
    dangerous_goods_acknowledged: bool = False


class DraftComposer:
    def compose(self, item: ItemForDrafting) -> ListingDraft:
        if not item.defects.strip():
            raise DraftValidationError(
                "known defects must be preserved: describe them or state "
                "'No known defects' explicitly"
            )
        if not item.category_id:
            raise DraftValidationError("a category is required before drafting")
        if not item.condition_id:
            raise DraftValidationError("a condition is required before drafting")
        if not (item.packed_weight_kg and item.length_cm and item.width_cm and item.height_cm):
            raise DraftValidationError("confirmed packed weight and dimensions are required")
        if item.restricted_items and not item.dangerous_goods_acknowledged:
            raise DraftValidationError(
                "dangerous-goods items require explicit seller acknowledgement"
            )
        if not item.shipping_recommendations:
            raise DraftValidationError("at least one shipping recommendation is required")
        for recommendation in item.shipping_recommendations:
            if not recommendation.publishable:
                raise DraftValidationError(
                    f"shipping for zone {recommendation.zone.value} is not publishable "
                    "(no fresh, seller-confirmed rate selected)"
                )

        return ListingDraft(
            sku=item.sku,
            marketplace_id=MARKETPLACE_ID,
            title=item.description.strip()[:MAX_TITLE_LENGTH],
            category_id=item.category_id,
            condition_id=item.condition_id,
            condition_description=item.defects,
            description=item.description,
            quantity=item.quantity,
            price=item.target_price,
            payment_policy_id=item.payment_policy_id,
            return_policy_id=item.return_policy_id,
            fulfillment_policy_id=item.fulfillment_policy_id,
            merchant_location_key=item.merchant_location_key,
            packed_weight_kg=item.packed_weight_kg,
            length_cm=item.length_cm,
            width_cm=item.width_cm,
            height_cm=item.height_cm,
        )
