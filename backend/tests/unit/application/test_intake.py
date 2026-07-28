import io
from decimal import Decimal

import pytest
from PIL import Image

from app.application.intake import IntakeService, IntakeValidationError, Upload
from app.domain.common import Money
from app.persistence.database import create_session_factory
from app.persistence.models import Base


def _jpeg_bytes(size: tuple[int, int] = (32, 32)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(200, 100, 50)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def jpeg_bytes() -> bytes:
    return _jpeg_bytes()


@pytest.fixture
def intake_service(tmp_path):
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    return IntakeService(session_factory=factory, photo_storage_dir=tmp_path / "uploads")


def test_intake_requires_defect_acknowledgement(intake_service, jpeg_bytes):
    with pytest.raises(IntakeValidationError, match="defects acknowledgement"):
        intake_service.create(
            description="Vintage lamp",
            defects=None,
            target_price=Money("EUR", Decimal("80.00")),
            photos=[Upload("lamp.jpg", "image/jpeg", jpeg_bytes)],
        )


def test_intake_requires_at_least_one_photo(intake_service):
    with pytest.raises(IntakeValidationError, match="photo"):
        intake_service.create(
            description="Vintage lamp",
            defects="No known defects",
            target_price=Money("EUR", Decimal("80.00")),
            photos=[],
        )


def test_intake_rejects_unsupported_image_type(intake_service):
    with pytest.raises(IntakeValidationError, match="unsupported image type"):
        intake_service.create(
            description="Vintage lamp",
            defects="No known defects",
            target_price=Money("EUR", Decimal("80.00")),
            photos=[Upload("lamp.gif", "image/gif", b"not-a-real-gif")],
        )


def test_intake_rejects_content_that_does_not_match_claimed_type(intake_service):
    with pytest.raises(IntakeValidationError, match="does not match"):
        intake_service.create(
            description="Vintage lamp",
            defects="No known defects",
            target_price=Money("EUR", Decimal("80.00")),
            photos=[Upload("lamp.jpg", "image/jpeg", b"this is not actually a jpeg")],
        )


def test_intake_stores_item_and_content_addressed_photo(intake_service, jpeg_bytes):
    item_id = intake_service.create(
        description="Vintage lamp",
        defects="Small scratch on the base",
        target_price=Money("EUR", Decimal("80.00")),
        photos=[Upload("lamp.jpg", "image/jpeg", jpeg_bytes)],
    )
    assert item_id

    second_item_id = intake_service.create(
        description="Another vintage lamp",
        defects="No known defects",
        target_price=Money("EUR", Decimal("50.00")),
        photos=[Upload("lamp.jpg", "image/jpeg", jpeg_bytes)],
    )
    assert item_id != second_item_id
