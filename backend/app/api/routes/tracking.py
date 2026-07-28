from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.tracking import (
    TrackingRefreshTrigger,
    TrackingService,
    TrackingValidationError,
)
from app.domain.tracking import TrackingDirection

router = APIRouter()


@router.post("/api/tracking")
async def add_tracking(
    request: Request,
    direction: TrackingDirection,
    carrier: str,
    tracking_number: str,
    label: str,
    item_id: str | None = None,
) -> JSONResponse:
    tracking_service: TrackingService = request.app.state.tracking_service
    try:
        record = tracking_service.add(direction, carrier, tracking_number, label, item_id)
    except TrackingValidationError as error:
        return JSONResponse(status_code=422, content={"detail": str(error)})
    return JSONResponse(
        status_code=201,
        content={
            "id": record.id,
            "direction": record.direction.value,
            "status": record.status.value,
        },
    )


@router.get("/api/tracking")
async def list_tracking(request: Request) -> JSONResponse:
    tracking_service: TrackingService = request.app.state.tracking_service
    records = tracking_service.list_all()
    return JSONResponse(
        status_code=200,
        content=[
            {
                "id": record.id,
                "direction": record.direction.value,
                "carrier": record.carrier,
                "tracking_number": record.tracking_number,
                "label": record.label,
                "item_id": record.item_id,
                "status": record.status.value,
                "last_refreshed_at": (
                    record.last_refreshed_at.isoformat() if record.last_refreshed_at else None
                ),
            }
            for record in records
        ],
    )


@router.post("/api/tracking/{record_id}/refresh")
async def refresh_tracking(record_id: str, request: Request) -> JSONResponse:
    tracking_service: TrackingService = request.app.state.tracking_service
    summary = await tracking_service.refresh(TrackingRefreshTrigger.MANUAL, record_id=record_id)
    return JSONResponse(
        status_code=200,
        content={"checked": summary.checked, "updated": summary.updated},
    )
