from dataclasses import dataclass

from app.domain.common import Money


@dataclass(frozen=True)
class ListingDraft:
    sku: str
    marketplace_id: str
    title: str
    category_id: str
    condition_id: str
    condition_description: str
    description: str
    quantity: int
    price: Money
    payment_policy_id: str
    return_policy_id: str
    fulfillment_policy_id: str
    merchant_location_key: str
    packed_weight_kg: str
    length_cm: str
    width_cm: str
    height_cm: str
