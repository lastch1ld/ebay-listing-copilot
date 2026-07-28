from decimal import Decimal

import pytest

from app.application.intake import IntakeService, Upload
from app.application.research import (
    ItemResearchRequest,
    ItemResearchResult,
    ResearchService,
)
from app.domain.common import Money, Provenance, SourcedValue
from app.persistence.database import create_session_factory
from app.persistence.models import Base, ResearchClaimModel


class FakeResearchClient:
    def __init__(self) -> None:
        self.result: ItemResearchResult | None = None
        self.last_request: ItemResearchRequest | None = None

    async def research_item(self, request: ItemResearchRequest) -> ItemResearchResult:
        self.last_request = request
        assert self.result is not None
        return self.result


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    return factory


@pytest.fixture
def fake_client() -> FakeResearchClient:
    return FakeResearchClient()


@pytest.fixture
def existing_item_id(session_factory, tmp_path) -> str:
    intake_service = IntakeService(
        session_factory=session_factory, photo_storage_dir=tmp_path / "uploads"
    )
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, format="JPEG")
    return intake_service.create(
        description="Vintage lamp",
        defects="No known defects",
        target_price=Money("EUR", Decimal("80.00")),
        photos=[Upload("lamp.jpg", "image/jpeg", buffer.getvalue())],
    )


@pytest.fixture
def research_service(session_factory, fake_client) -> ResearchService:
    return ResearchService(client=fake_client, session_factory=session_factory)


@pytest.mark.asyncio
async def test_research_never_upgrades_inference_to_verified(
    fake_client, research_service, existing_item_id
):
    fake_client.result = ItemResearchResult(
        identity=SourcedValue("Model X", Provenance.INFERRED, Decimal("0.65"), ()),
        comparable_prices=(Money("EUR", Decimal("75.00")),),
        warnings=(),
        questions=(),
    )
    result = await research_service.run(item_id=existing_item_id)
    assert result.identity.provenance is Provenance.INFERRED
    assert result.identity.sources == ()


@pytest.mark.asyncio
async def test_research_persists_claim_with_provenance(
    fake_client, research_service, existing_item_id, session_factory
):
    fake_client.result = ItemResearchResult(
        identity=SourcedValue(
            "Model X", Provenance.SOURCE_VERIFIED, Decimal("0.95"), ("https://example.invalid/x",)
        ),
        comparable_prices=(),
        warnings=(),
        questions=(),
    )
    await research_service.run(item_id=existing_item_id)

    with session_factory() as session:
        claims = session.query(ResearchClaimModel).filter_by(item_id=existing_item_id).all()
    assert len(claims) == 1
    assert claims[0].provenance == "SOURCE_VERIFIED"


@pytest.mark.asyncio
async def test_research_builds_request_from_stored_item(
    fake_client, research_service, existing_item_id
):
    fake_client.result = ItemResearchResult(
        identity=SourcedValue(None, Provenance.UNKNOWN, Decimal("0")),
        comparable_prices=(),
        warnings=(),
        questions=("What is the manufacturer?",),
    )
    await research_service.run(item_id=existing_item_id)
    assert fake_client.last_request is not None
    assert fake_client.last_request.description == "Vintage lamp"
    assert fake_client.last_request.defects == "No known defects"
