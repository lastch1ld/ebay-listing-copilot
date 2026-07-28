import pytest
from fastapi.testclient import TestClient

from app.application.intake import IntakeService
from app.application.jobs import JobRunner
from app.application.research import ResearchService
from app.integrations.openai.research import UnconfiguredResearchClient
from app.main import app
from app.persistence.database import create_session_factory
from app.persistence.models import Base, JobModel


@pytest.fixture
def client(tmp_path):
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    app.state.session_factory = factory
    app.state.intake_service = IntakeService(
        session_factory=factory, photo_storage_dir=tmp_path / "uploads"
    )
    app.state.job_runner = JobRunner(session_factory=factory)
    app.state.research_service = ResearchService(
        client=UnconfiguredResearchClient(), session_factory=factory
    )
    return TestClient(app)


def _create_item(client: TestClient) -> str:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, format="JPEG")
    response = client.post(
        "/api/items",
        data={
            "description": "Vintage lamp",
            "defects": "No known defects",
            "target_price_currency": "EUR",
            "target_price_value": "80.00",
        },
        files={"photos": ("lamp.jpg", buffer.getvalue(), "image/jpeg")},
    )
    return str(response.json()["item_id"])


def test_start_research_returns_404_for_unknown_item(client: TestClient) -> None:
    response = client.post("/api/items/does-not-exist/research")
    assert response.status_code == 404


def test_start_research_returns_202_and_enqueues_job(client: TestClient) -> None:
    item_id = _create_item(client)

    response = client.post(f"/api/items/{item_id}/research")

    assert response.status_code == 202
    assert response.json()["item_id"] == item_id

    with app.state.session_factory() as session:
        job = session.get(JobModel, response.json()["job_id"])
        assert job is not None
        assert job.job_type == "ITEM_RESEARCH"
        assert job.status == "PENDING"
        assert job.error_json is not None
        assert "OPENAI_API_KEY" in job.error_json
