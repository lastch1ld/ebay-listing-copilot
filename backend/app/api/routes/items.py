from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.application.intake import IntakeService, IntakeValidationError, Upload
from app.domain.common import Money

router = APIRouter()


@router.post("/api/items")
async def create_item(
    request: Request,
    description: str = Form(...),
    defects: str | None = Form(None),
    target_price_currency: str = Form(...),
    target_price_value: str = Form(...),
    photos: list[UploadFile] = File(default_factory=list),
) -> JSONResponse:
    intake_service: IntakeService = request.app.state.intake_service

    try:
        target_price = Money(target_price_currency, Decimal(target_price_value))
    except (InvalidOperation, ValueError) as error:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    uploads = [
        Upload(
            filename=photo.filename or "",
            mime_type=photo.content_type or "",
            content=await photo.read(),
        )
        for photo in photos
    ]

    try:
        item_id = intake_service.create(
            description=description,
            defects=defects,
            target_price=target_price,
            photos=uploads,
        )
    except IntakeValidationError as error:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    return JSONResponse(status_code=201, content={"item_id": item_id})
