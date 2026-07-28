from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes.activity import router as activity_router
from app.api.routes.auth import router as auth_router
from app.api.routes.drafts import router as drafts_router
from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.api.routes.research import router as research_router
from app.api.routes.tracking import router as tracking_router
from app.application.activity import ActivityService, RefreshTrigger
from app.application.approval import ApprovalService
from app.application.intake import IntakeService
from app.application.jobs import JobRunner
from app.application.publishing import PublishingService
from app.application.research import ResearchClient, ResearchService
from app.application.tracking import TrackingRefreshTrigger, TrackingService
from app.config import load_settings
from app.integrations.ebay.fulfillment import EbayFulfillmentOrdersSource
from app.integrations.ebay.inventory import EbayInventoryClient
from app.integrations.ebay.oauth import EbayOAuth, EbayTokenStore
from app.integrations.ebay.rest import EbayRestClient
from app.integrations.ebay.trading import EbayTradingBestOffersSource
from app.integrations.openai.research import OpenAIResearchClient, UnconfiguredResearchClient
from app.integrations.tracking.base import TrackingProvider
from app.integrations.tracking.carrier_adapter import (
    AggregatorTrackingProvider,
    UnconfiguredTrackingProvider,
)
from app.persistence.database import create_session_factory
from app.security.secrets import SecretStore

_EBAY_SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
)

settings = load_settings()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    job_runner: JobRunner = app.state.job_runner
    activity_service: ActivityService = app.state.activity_service
    tracking_service: TrackingService = app.state.tracking_service
    job_runner.enqueue("STARTUP_ACTIVITY_REFRESH", {})
    job_runner.enqueue("LOGIN_TRACKING_REFRESH", {})

    async def handle_activity(_input_data: dict[str, object]) -> str | None:
        await activity_service.refresh(RefreshTrigger.STARTUP)
        return None

    async def handle_tracking(_input_data: dict[str, object]) -> str | None:
        await tracking_service.refresh(TrackingRefreshTrigger.LOGIN)
        return None

    await job_runner.process_due(
        {
            "STARTUP_ACTIVITY_REFRESH": handle_activity,
            "LOGIN_TRACKING_REFRESH": handle_tracking,
        }
    )
    yield


app = FastAPI(title="eBay Listing Copilot", lifespan=_lifespan)
app.include_router(health_router)
app.include_router(items_router)
app.include_router(research_router)
app.include_router(auth_router)
app.include_router(drafts_router)
app.include_router(activity_router)
app.include_router(tracking_router)

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

app.state.ebay_oauth = EbayOAuth(
    client_id=settings.ebay_client_id,
    client_secret=settings.ebay_client_secret.get_secret_value(),
    redirect_uri=settings.ebay_redirect_uri,
    environment=settings.ebay_environment,
    scopes=_EBAY_SCOPES,
    token_store=EbayTokenStore(SecretStore(service="ebay-listing-copilot")),
)


def _ebay_access_token() -> str:
    oauth: EbayOAuth = app.state.ebay_oauth
    return oauth.refresh().access_token


app.state.approval_service = ApprovalService(session_factory=app.state.session_factory)
_ebay_rest_client = EbayRestClient(
    environment=settings.ebay_environment, access_token_provider=_ebay_access_token
)
app.state.publishing_service = PublishingService(
    session_factory=app.state.session_factory,
    ebay_client=EbayInventoryClient(_ebay_rest_client),
)
app.state.activity_service = ActivityService(
    session_factory=app.state.session_factory,
    sources=[
        EbayTradingBestOffersSource(_ebay_rest_client),
        EbayFulfillmentOrdersSource(_ebay_rest_client),
    ],
)

tracking_provider: TrackingProvider
if settings.tracking_provider_base_url:
    tracking_provider = AggregatorTrackingProvider(settings.tracking_provider_base_url)
else:
    tracking_provider = UnconfiguredTrackingProvider()

app.state.tracking_service = TrackingService(
    session_factory=app.state.session_factory,
    provider=tracking_provider,
)
