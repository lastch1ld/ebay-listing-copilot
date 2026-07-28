from pathlib import Path

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.application.intake import IntakeService
from app.config import load_settings
from app.persistence.database import create_session_factory

settings = load_settings()

app = FastAPI(title="eBay Listing Copilot")
app.include_router(health_router)
app.include_router(items_router)

app.state.session_factory = create_session_factory(settings.database_url)
app.state.intake_service = IntakeService(
    session_factory=app.state.session_factory,
    photo_storage_dir=Path("data/uploads"),
)
