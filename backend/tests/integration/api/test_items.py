import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.application.intake import IntakeService
from app.main import app
from app.persistence.database import create_session_factory
from app.persistence.models import Base


@pytest.fixture
def client(tmp_path):
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    app.state.session_factory = factory
    app.state.intake_service = IntakeService(
        session_factory=factory, photo_storage_dir=tmp_path / "uploads"
    )
    return TestClient(app)


def _jpeg_upload_file() -> tuple[str, io.BytesIO, str]:
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(buffer, format="JPEG")
    buffer.seek(0)
    return "lamp.jpg", buffer, "image/jpeg"


def test_create_item_accepts_valid_multipart_request(client: TestClient) -> None:
    filename, file_obj, content_type = _jpeg_upload_file()
    response = client.post(
        "/api/items",
        data={
            "description": "Vintage lamp",
            "defects": "No known defects",
            "target_price_currency": "EUR",
            "target_price_value": "80.00",
        },
        files={"photos": (filename, file_obj, content_type)},
    )
    assert response.status_code == 201
    assert response.json()["item_id"]


def test_create_item_rejects_missing_defects_acknowledgement(client: TestClient) -> None:
    filename, file_obj, content_type = _jpeg_upload_file()
    response = client.post(
        "/api/items",
        data={
            "description": "Vintage lamp",
            "target_price_currency": "EUR",
            "target_price_value": "80.00",
        },
        files={"photos": (filename, file_obj, content_type)},
    )
    assert response.status_code == 422
    assert "defects acknowledgement" in response.json()["detail"]
