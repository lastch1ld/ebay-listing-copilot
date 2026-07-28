from pathlib import Path

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.api.routes.research import router as research_router
from app.application.intake import IntakeService
from app.application.jobs import JobRunner
from app.application.research import ResearchClient, ResearchService
from app.config import load_settings
from app.integrations.openai.research import OpenAIResearchClient, UnconfiguredResearchClient
from app.persistence.database import create_session_factory

settings = load_settings()

app = FastAPI(title="eBay Listing Copilot")
app.include_router(health_router)
app.include_router(items_router)
app.include_router(research_router)

app.state.session_factory = create_session_factory(settings.database_url)
app.state.intake_service = IntakeService(
    session_factory=app.state.session_factory,
    photo_storage_dir=Path("data/uploads"),
)
app.state.job_runner = JobRunner(session_factory=app.state.session_factory)

research_client: ResearchClient
if settings.openai_api_key.get_secret_value() and settings.openai_model:
    research_client = OpenAIResearchClient(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
    )
else:
    research_client = UnconfiguredResearchClient()

app.state.research_service = ResearchService(
    client=research_client,
    session_factory=app.state.session_factory,
)
