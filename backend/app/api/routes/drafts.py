from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.approval import ApprovalService
from app.application.publishing import PublishingService
from app.domain.draft import ListingDraft

router = APIRouter()


@router.post("/api/items/{item_id}/approve")
async def approve_draft(item_id: str, draft: ListingDraft, request: Request) -> JSONResponse:
    approval_service: ApprovalService = request.app.state.approval_service
    approval = approval_service.approve(item_id, draft)
    return JSONResponse(
        status_code=200,
        content={
            "draft_version_id": approval.draft_version_id,
            "payload_hash": approval.payload_hash,
        },
    )


@router.post("/api/items/{item_id}/publish")
async def publish_draft(
    item_id: str, offer_id: str, draft_hash: str, request: Request
) -> JSONResponse:
    publishing_service: PublishingService = request.app.state.publishing_service
    listing_ref = publishing_service.publish(offer_id=offer_id, draft_hash=draft_hash)
    return JSONResponse(
        status_code=200,
        content={
            "listing_id": listing_ref.listing_id,
            "listing_url": listing_ref.listing_url,
        },
    )
