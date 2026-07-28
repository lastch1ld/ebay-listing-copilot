from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.activity import ActivityService, RefreshTrigger

router = APIRouter()


@router.post("/api/activity/refresh")
async def refresh_activity(request: Request) -> JSONResponse:
    activity_service: ActivityService = request.app.state.activity_service
    summary = await activity_service.refresh(RefreshTrigger.LISTING_MUTATION)
    return JSONResponse(
        status_code=200,
        content={"created": summary.created, "failed_sources": list(summary.failed_sources)},
    )
