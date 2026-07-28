from app.application.activity import ActivityService, RefreshTrigger
from app.application.approval import Approval, ApprovalService, DraftVersion
from app.domain.draft import ListingDraft
from app.integrations.ebay.inventory import EbayInventoryClient
from app.persistence.database import SessionFactory
from app.persistence.repositories import ApprovalRepository, OperationRepository


class RevisionNotApprovedError(ValueError):
    pass


class ListingManagementService:
    def __init__(
        self,
        session_factory: SessionFactory,
        ebay_client: EbayInventoryClient,
        activity_service: ActivityService,
    ) -> None:
        self._approval_service = ApprovalService(session_factory)
        self._approval_repository = ApprovalRepository(session_factory)
        self._operations = OperationRepository(session_factory)
        self._ebay_client = ebay_client
        self._activity_service = activity_service

    def propose_revision(self, item_id: str, draft: ListingDraft) -> DraftVersion:
        """Creates a new canonical draft version; it is not yet approved."""
        return self._approval_service.create_draft_version(item_id, draft)

    async def apply_approved_revision(
        self, offer_id: str, approval: Approval, draft: ListingDraft
    ) -> None:
        stored_approval = self._approval_repository.for_draft_version(approval.draft_version_id)
        if stored_approval is None or stored_approval.payload_hash != approval.payload_hash:
            raise RevisionNotApprovedError(
                "the draft must be approved before it can be applied"
            )
        if not self._approval_service.matches(approval, draft):
            raise RevisionNotApprovedError(
                "the draft has changed since approval; reapprove before applying"
            )

        operation_key = f"revise:{offer_id}:{approval.payload_hash}"
        operation = self._operations.begin(operation_key)
        if operation.status != "COMPLETED":
            self._ebay_client.update_offer(offer_id, draft)
            self._operations.complete(operation.id, "{}")

        await self._activity_service.refresh(RefreshTrigger.LISTING_MUTATION)

    async def withdraw_approved_listing(self, offer_id: str, action_summary_hash: str) -> None:
        operation_key = f"withdraw:{offer_id}:{action_summary_hash}"
        operation = self._operations.begin(operation_key)
        if operation.status != "COMPLETED":
            self._ebay_client.withdraw_offer(offer_id)
            self._operations.complete(operation.id, "{}")

        await self._activity_service.refresh(RefreshTrigger.LISTING_MUTATION)
