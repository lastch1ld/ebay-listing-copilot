from dataclasses import dataclass

from app.integrations.ebay.rest import EbayRestClient

MARKETPLACE_ID = "EBAY_IT"


@dataclass(frozen=True)
class AccountReadiness:
    marketplace_id: str
    has_payment_policy: bool
    has_return_policy: bool
    has_fulfillment_policy: bool
    has_inventory_location: bool
    missing_steps: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return not self.missing_steps


class EbayAccountClient:
    def __init__(self, rest_client: EbayRestClient, marketplace_id: str = MARKETPLACE_ID) -> None:
        self._rest_client = rest_client
        self._marketplace_id = marketplace_id

    def readiness(self) -> AccountReadiness:
        payment_policies = self._count(
            "/sell/account/v1/payment_policy", "paymentPolicies"
        )
        return_policies = self._count("/sell/account/v1/return_policy", "returnPolicies")
        fulfillment_policies = self._count(
            "/sell/account/v1/fulfillment_policy", "fulfillmentPolicies"
        )
        inventory_locations = self._count(
            "/sell/inventory/v1/location", "locations", root_path=None
        )

        missing_steps: list[str] = []
        if payment_policies == 0:
            missing_steps.append("Create a payment policy for EBAY_IT in Seller Hub.")
        if return_policies == 0:
            missing_steps.append("Create a return policy for EBAY_IT in Seller Hub.")
        if fulfillment_policies == 0:
            missing_steps.append("Create a fulfillment (shipping) policy for EBAY_IT.")
        if inventory_locations == 0:
            missing_steps.append("Create at least one inventory location.")

        return AccountReadiness(
            marketplace_id=self._marketplace_id,
            has_payment_policy=payment_policies > 0,
            has_return_policy=return_policies > 0,
            has_fulfillment_policy=fulfillment_policies > 0,
            has_inventory_location=inventory_locations > 0,
            missing_steps=tuple(missing_steps),
        )

    def _count(self, path: str, list_key: str, root_path: str | None = "default") -> int:
        params = {"marketplace_id": self._marketplace_id} if root_path == "default" else None
        payload = self._rest_client.get(path, params=params)
        entries = payload.get(list_key, [])
        if isinstance(entries, list):
            return len(entries)
        return 0
