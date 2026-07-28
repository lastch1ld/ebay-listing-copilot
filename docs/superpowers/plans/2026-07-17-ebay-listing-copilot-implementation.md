# eBay Listing Copilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a private local web application that turns item photos, a description, and a target price into a researched, shipping-aware eBay draft; publishes only the exact approved version; manages later revisions; shows one-time offer, sale, and refund notifications; and tracks seller-entered shipment tracking numbers with a status refresh on login.

**Architecture:** Use a React/TypeScript frontend and a FastAPI/Python backend bound to loopback. Keep domain rules independent of providers, persist workflow state in SQLite, store credentials in the operating-system keychain, and place eBay, OpenAI, shipping, and carrier-tracking behavior behind typed adapters. Use eBay Inventory offers as unpublished eBay drafts, Media for photos, Account for policies, Fulfillment for orders/refunds, and Trading `GetBestOffers` for buyer offers.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, httpx, keyring, pytest, respx; Node.js 22+, React, TypeScript, Vite, TanStack Query, Vitest, Testing Library, Playwright; SQLite; OpenAI Responses API adapter; eBay REST and Trading APIs; GitHub Actions.

## Global Constraints

- Follow `AGENTS.md` for every task.
- Bind the backend to `127.0.0.1`; do not expose a network listener publicly.
- Never collect or store account passwords. Store OAuth refresh tokens and provider secrets in the OS keychain.
- Use fictional fixtures only. Never commit tokens, seller data, photos, databases, provider payloads, or logs.
- Preserve known defects through intake, research, draft, approval, and publication.
- Label every researched field `USER_PROVIDED`, `OBSERVED`, `SOURCE_VERIFIED`, `INFERRED`, or `UNKNOWN`.
- Keep the user's target price unless the user explicitly chooses a different recommendation.
- Block publication until package weight and dimensions are confirmed and shipping prices are fresh.
- Cover Italy, EU continental Europe, and non-EU continental Europe as separate shipping zones.
- Bind approval to the SHA-256 hash of the canonical normalized action payload; any material change invalidates approval.
- Use idempotency records and reconciliation before retrying an ambiguous eBay mutation.
- Refresh offers, sales, and refunds once at app startup and once after successful listing mutations; do not poll continuously.
- Notification refresh is read-only and may not accept offers or issue refunds.
- Refresh open (undelivered) tracking records once on login and on demand per record; do not poll continuously.
- Tracking numbers are entered manually by the seller; the application never purchases labels or uploads tracking to eBay/buyers.
- Inventory API listings cannot be edited in Seller Hub; show this limitation before the first Production publish.
- Required CI must be credential-free. Credentialed eBay Sandbox tests run only through a protected manual workflow.

---

## Planned file structure

```text
ebay-listing-copilot/
├── .github/workflows/ci.yml
├── .github/workflows/sandbox-e2e.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/routes/{health,items,research,drafts,activity,tracking,auth}.py
│   │   ├── domain/{common,item,draft,shipping,activity,tracking,state}.py
│   │   ├── application/{intake,jobs,research,drafting,approval,publishing,listing_management,activity,tracking}.py
│   │   ├── integrations/ebay/{oauth,rest,inventory,media,account,taxonomy,metadata,fulfillment,trading}.py
│   │   ├── integrations/openai/research.py
│   │   ├── integrations/shipping/{base,research,fixed_rates}.py
│   │   ├── integrations/tracking/{base,carrier_adapter}.py
│   │   ├── persistence/{database,models,repositories,migrations}.py
│   │   └── security/{secrets,redaction}.py
│   └── tests/{unit,integration,contract,e2e}/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── api/client.ts
│   │   ├── app/router.tsx
│   │   ├── features/intake/
│   │   ├── features/research/
│   │   ├── features/review/
│   │   ├── features/listings/
│   │   ├── features/activity/
│   │   └── features/tracking/
│   └── tests/
└── scripts/{check_no_secrets.py,verify_no_production_calls.py}
```

## Task 1: Scaffold the local application and required credential-free CI

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/api/routes/health.py`
- Create: `backend/tests/unit/test_health.py`
- Create: `frontend/package.json`, `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- Create: `.gitignore`, `.env.example`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `GET /api/health -> {"status":"ok","environment":"sandbox"|"production"}`
- Produces: frontend application shell showing the active environment.

- [ ] **Step 1: Add the failing backend health test**

```python
# backend/tests/unit/test_health.py
from fastapi.testclient import TestClient
from app.main import app

def test_health_is_loopback_safe_and_reports_environment():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "sandbox"}
```

- [ ] **Step 2: Run the backend test and verify the missing app failure**

Run: `cd backend && python -m pytest tests/unit/test_health.py -q`  
Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Add the minimal FastAPI application**

```python
# backend/app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": "sandbox"}

# backend/app/main.py
from fastapi import FastAPI
from app.api.routes.health import router as health_router

app = FastAPI(title="eBay Listing Copilot")
app.include_router(health_router)
```

Configure `backend/pyproject.toml` with Python `>=3.12`, FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, keyring, pytest, pytest-asyncio, respx, Ruff, and mypy. Configure Ruff and mypy in strict mode.

- [ ] **Step 4: Add and test the frontend environment banner**

```tsx
// frontend/src/app/App.test.tsx
import { render, screen } from "@testing-library/react";
import { App } from "./App";

it("shows the active environment", () => {
  render(<App environment="sandbox" />);
  expect(screen.getByText("Sandbox")).toBeVisible();
});

// frontend/src/app/App.tsx
export function App({ environment }: { environment: "sandbox" | "production" }) {
  return <main><strong>{environment === "sandbox" ? "Sandbox" : "Production"}</strong></main>;
}
```

Run: `cd frontend && npm test -- --run`  
Expected: PASS.

- [ ] **Step 5: Add the credential-free GitHub Actions workflow**

Create `.github/workflows/ci.yml` with read-only permissions and jobs for backend Ruff, mypy, pytest, frontend formatting/lint/typecheck/Vitest/build, secret scan, and dependency scan. Pin every third-party action to a reviewed full commit SHA during implementation. Use `npm ci` and a committed lockfile; use Python dependency locking from `pyproject.toml`.

Run locally: `cd backend && python -m ruff check . && python -m mypy app && python -m pytest -q`  
Run locally: `cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build`  
Expected: all commands PASS.

- [ ] **Step 6: Commit the scaffold**

```bash
git add .gitignore .env.example .github backend frontend
git commit -m "chore: scaffold local listing copilot"
```

## Task 2: Define domain types, provenance, and workflow state

**Files:**
- Create: `backend/app/domain/common.py`, `state.py`
- Test: `backend/tests/unit/domain/test_state.py`, `test_provenance.py`, `test_money.py`

Note: `item.py` and `draft.py` are created later, in the tasks that first give them real content (item intake in Task 5, draft composition in Task 6), instead of as empty placeholders here.

**Interfaces:**
- Produces: `Money(currency: str, value: Decimal)`
- Produces: `SourcedValue[T](value, provenance, confidence, sources)`
- Produces: `ItemState` and `transition(current, target) -> ItemState`

- [ ] **Step 1: Write failing domain tests**

```python
from decimal import Decimal
import pytest
from app.domain.common import Money, Provenance, SourcedValue
from app.domain.state import ItemState, InvalidTransition, transition

def test_money_rejects_binary_float():
    with pytest.raises(TypeError):
        Money(currency="EUR", value=19.99)  # type: ignore[arg-type]

def test_inferred_value_retains_source_and_confidence():
    value = SourcedValue(value="Model X", provenance=Provenance.INFERRED,
                         confidence=Decimal("0.70"), sources=("https://example.invalid/model",))
    assert value.provenance is Provenance.INFERRED

def test_approved_draft_cannot_skip_to_live():
    with pytest.raises(InvalidTransition):
        transition(ItemState.APPROVED, ItemState.LIVE)
```

- [ ] **Step 2: Run tests and verify they fail on missing domain modules**

Run: `cd backend && python -m pytest tests/unit/domain -q`  
Expected: FAIL with import errors.

- [ ] **Step 3: Implement exact domain primitives and allowed transitions**

```python
# backend/app/domain/common.py
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Generic, TypeVar

T = TypeVar("T")

class Provenance(StrEnum):
    USER_PROVIDED = "USER_PROVIDED"
    OBSERVED = "OBSERVED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class Money:
    currency: str
    value: Decimal
    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError("Money.value must be Decimal")
        if len(self.currency) != 3 or self.currency.upper() != self.currency:
            raise ValueError("currency must be an uppercase ISO-4217 code")

@dataclass(frozen=True)
class SourcedValue(Generic[T]):
    value: T | None
    provenance: Provenance
    confidence: Decimal
    sources: tuple[str, ...] = ()

# backend/app/domain/state.py
from enum import StrEnum

class ItemState(StrEnum):
    INTAKE="INTAKE"; RESEARCHING="RESEARCHING"; NEEDS_INPUT="NEEDS_INPUT"
    DRAFTING="DRAFTING"; DRAFT_READY="DRAFT_READY"; EBAY_DRAFTED="EBAY_DRAFTED"
    AWAITING_APPROVAL="AWAITING_APPROVAL"; APPROVED="APPROVED"
    PUBLISHING="PUBLISHING"; LIVE="LIVE"; ACTION_REQUIRED="ACTION_REQUIRED"; FAILED="FAILED"

class InvalidTransition(ValueError): pass

ALLOWED = {
    ItemState.INTAKE: {ItemState.RESEARCHING},
    ItemState.RESEARCHING: {ItemState.NEEDS_INPUT, ItemState.DRAFTING, ItemState.ACTION_REQUIRED},
    ItemState.NEEDS_INPUT: {ItemState.RESEARCHING},
    ItemState.DRAFTING: {ItemState.DRAFT_READY, ItemState.ACTION_REQUIRED},
    ItemState.DRAFT_READY: {ItemState.EBAY_DRAFTED},
    ItemState.EBAY_DRAFTED: {ItemState.AWAITING_APPROVAL},
    ItemState.AWAITING_APPROVAL: {ItemState.APPROVED, ItemState.DRAFTING},
    ItemState.APPROVED: {ItemState.PUBLISHING, ItemState.AWAITING_APPROVAL},
    ItemState.PUBLISHING: {ItemState.LIVE, ItemState.ACTION_REQUIRED},
    ItemState.LIVE: {ItemState.DRAFTING, ItemState.ACTION_REQUIRED},
    ItemState.ACTION_REQUIRED: {ItemState.RESEARCHING, ItemState.DRAFTING, ItemState.PUBLISHING},
    ItemState.FAILED: set(),
}

def transition(current: ItemState, target: ItemState) -> ItemState:
    if target not in ALLOWED[current]:
        raise InvalidTransition(f"{current} -> {target} is not allowed")
    return target
```

- [ ] **Step 4: Run domain tests**

Run: `cd backend && python -m pytest tests/unit/domain -q`  
Expected: PASS.

- [ ] **Step 5: Commit domain types**

```bash
git add backend/app/domain backend/tests/unit/domain
git commit -m "feat: add listing workflow domain model"
```

## Task 3: Add SQLite persistence, migrations, operation records, and repositories

**Files:**
- Create: `backend/app/persistence/database.py`, `models.py`, `repositories.py`
- Create: `backend/migrations/env.py`, `backend/migrations/versions/0001_initial.py`
- Test: `backend/tests/integration/test_repositories.py`

**Interfaces:**
- Consumes: `Money`, `ItemState`, draft identifiers.
- Produces: `ItemRepository`, `DraftRepository`, `ApprovalRepository`, `OperationRepository`, `ActivityRepository`.

- [ ] **Step 1: Write a failing repository transaction test**

```python
def test_operation_key_is_unique_and_survives_restart(session_factory):
    first = OperationRepository(session_factory).begin("publish:item-1:draft-3")
    second = OperationRepository(session_factory).begin("publish:item-1:draft-3")
    assert first.id == second.id
    assert second.status == "PENDING"
```

- [ ] **Step 2: Run the test and verify missing repository failure**

Run: `cd backend && python -m pytest tests/integration/test_repositories.py -q`  
Expected: FAIL because persistence modules do not exist.

- [ ] **Step 3: Implement models and initial migration**

Create normalized tables for `items`, `photos`, `research_claims`, `draft_versions`, `approvals`, `operations`, `jobs`, `shipping_quotes`, `activity_events`, and `checkpoints`. Required constraints: unique draft version per item, unique operation key, unique activity deduplication key, UTC timestamps, and foreign keys enabled. A job row records type, serialized validated input, status, attempt count, next-attempt time, lease expiry, result reference, and normalized error.

```python
# backend/app/persistence/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

def create_session_factory(url: str):
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")
    return sessionmaker(engine, expire_on_commit=False)
```

Implement repository methods so `begin(key)` inserts once and returns the existing row on a uniqueness conflict in a new transaction.

- [ ] **Step 4: Apply migration and run repository tests**

Run: `cd backend && python -m alembic upgrade head && python -m pytest tests/integration/test_repositories.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit persistence**

```bash
git add backend/app/persistence backend/migrations backend/alembic.ini backend/tests/integration
git commit -m "feat: persist listing workflow state"
```

## Task 4: Enforce configuration, keychain storage, and redacted logging

**Files:**
- Create: `backend/app/config.py`, `backend/app/security/secrets.py`, `redaction.py`
- Create: `scripts/check_no_secrets.py`
- Test: `backend/tests/unit/security/test_secrets.py`, `test_redaction.py`

**Interfaces:**
- Produces: `SecretStore.get/set/delete(name)` and `redact_mapping(value) -> dict`.

- [ ] **Step 1: Write tests that prohibit token leakage**

```python
def test_redaction_removes_nested_tokens():
    safe = redact_mapping({"Authorization":"Bearer abc", "buyer":{"email":"a@b.test"}, "status":"ok"})
    assert safe == {"Authorization":"[REDACTED]", "buyer":{"email":"[REDACTED]"}, "status":"ok"}

def test_secret_store_uses_named_keyring(fake_keyring):
    store = SecretStore(service="ebay-listing-copilot-test", backend=fake_keyring)
    store.set("ebay.refresh_token", "secret")
    assert store.get("ebay.refresh_token") == "secret"
```

- [ ] **Step 2: Implement an injectable keyring wrapper and recursive allowlist redactor**

Keep secret values out of Pydantic settings serialization and `repr`. Reject Production startup when a file-backed test secret backend is configured.

- [ ] **Step 3: Add repository secret scanner script**

`scripts/check_no_secrets.py` must scan tracked files and fail on configured eBay/OpenAI key patterns, bearer tokens, private keys, non-example `.env` files, SQLite files, and uploads. It must ignore only explicit fictional fixtures marked `SAFE_FAKE_CREDENTIAL`.

- [ ] **Step 4: Run security tests and scanner**

Run: `cd backend && python -m pytest tests/unit/security -q`  
Run: `python scripts/check_no_secrets.py`  
Expected: PASS and `No tracked secrets or private runtime files found`.

- [ ] **Step 5: Commit security foundation**

```bash
git add backend/app/config.py backend/app/security backend/tests/unit/security scripts
git commit -m "security: protect credentials and redact logs"
```

## Task 5: Implement item intake and immutable photo storage

**Files:**
- Create: `backend/app/application/intake.py`, `backend/app/api/routes/items.py`
- Create: `backend/tests/unit/application/test_intake.py`, `backend/tests/integration/api/test_items.py`
- Create: `frontend/src/features/intake/ItemIntakeForm.tsx`, `ItemIntakeForm.test.tsx`

**Interfaces:**
- Produces: `IntakeService.create(description, defects, target_price, photos) -> ItemId`.
- Produces: `POST /api/items` multipart endpoint.

- [ ] **Step 1: Test rejection of missing defects acknowledgement and invalid images**

```python
def test_intake_requires_defect_acknowledgement(intake_service, jpeg_bytes):
    with pytest.raises(IntakeValidationError, match="defects acknowledgement"):
        intake_service.create(description="Vintage lamp", defects=None,
                              target_price=Money("EUR", Decimal("80.00")),
                              photos=[Upload("lamp.jpg", "image/jpeg", jpeg_bytes)])
```

- [ ] **Step 2: Implement intake validation and content-addressed photo storage**

Accept JPEG, PNG, and WebP only; enforce per-file and total-size limits; verify decoded image type; generate a SHA-256 content ID; store originals under the untracked runtime directory; never overwrite originals; persist filename, MIME type, hash, size, and dimensions.

- [ ] **Step 3: Add the typed frontend form**

The form must require description, target price, currency `EUR`, at least one photo, and either defect text or an explicit `No known defects` acknowledgement. Display upload errors without logging image content.

- [ ] **Step 4: Run backend and frontend intake tests**

Run: `cd backend && python -m pytest tests/unit/application/test_intake.py tests/integration/api/test_items.py -q`  
Run: `cd frontend && npm test -- --run ItemIntakeForm`  
Expected: PASS.

- [ ] **Step 5: Commit intake**

```bash
git add backend/app/application/intake.py backend/app/api/routes/items.py backend/tests frontend/src/features/intake
git commit -m "feat: add safe item intake"
```

## Task 6: Build source-backed item and price research

**Files:**
- Create: `backend/app/application/research.py`
- Create: `backend/app/integrations/openai/research.py`
- Create: `backend/app/application/jobs.py`, `backend/app/api/routes/research.py`
- Test: `backend/tests/unit/application/test_research.py`, `backend/tests/contract/test_openai_research.py`

**Interfaces:**
- Produces: `ResearchClient.research_item(ItemResearchRequest) -> ItemResearchResult`.
- Produces: sourced identity, specifications, category candidates, comparable listings, price range, warnings, and missing questions.

- [ ] **Step 1: Define and test the research contract**

```python
async def test_research_never_upgrades_inference_to_verified(fake_client, research_service):
    fake_client.result = ItemResearchResult(
        identity=SourcedValue("Model X", Provenance.INFERRED, Decimal("0.65"), ()),
        comparable_prices=(Money("EUR", Decimal("75.00")),), warnings=(), questions=())
    result = await research_service.run(item_id="item-1")
    assert result.identity.provenance is Provenance.INFERRED
    assert result.identity.sources == ()
```

- [ ] **Step 2: Implement the application service with a provider interface**

The service sends reduced image inputs, user description, defects, and target price; requires JSON-schema output; validates URLs and provenance; stores short factual claims and source URLs; and creates questions for any required field with `UNKNOWN` or low confidence.

- [ ] **Step 3: Implement the OpenAI Responses adapter**

Use the configured `OPENAI_MODEL` with no hard-coded fallback. Send images and text, enable the provider's supported web-search tool, request strict structured output, and extract cited source URLs. Reject a result that labels a value `SOURCE_VERIFIED` without at least one valid HTTPS source. The contract test must use a mocked SDK transport and no network.

- [ ] **Step 4: Persist and resume research jobs**

`POST /api/items/{item_id}/research` creates one active `ITEM_RESEARCH` job per item and returns `202`. `JobRunner` leases due jobs transactionally, renews leases during work, records bounded retry timing for transient failures, and resumes expired leases after restart. Add a test that stops after leasing, creates a new runner, advances the clock beyond lease expiry, and verifies the job completes once.

- [ ] **Step 5: Run research tests**

Run: `cd backend && python -m pytest tests/unit/application/test_research.py tests/contract/test_openai_research.py tests/integration/test_jobs.py -q`  
Expected: PASS.

- [ ] **Step 6: Commit research**

```bash
git add backend/app/application/research.py backend/app/application/jobs.py backend/app/api/routes/research.py backend/app/integrations/openai backend/tests
git commit -m "feat: add source-backed item research"
```

## Task 7: Implement Italy, EU, and non-EU shipping research

**Files:**
- Create: `backend/app/domain/shipping.py`
- Create: `backend/app/integrations/shipping/base.py`, `research.py`, `fixed_rates.py`
- Create: `backend/app/application/shipping.py`
- Test: `backend/tests/unit/shipping/test_zones.py`, `test_quotes.py`, `test_freshness.py`

**Interfaces:**
- Produces: `ShippingZone.ITALY`, `EU_CONTINENTAL`, `NON_EU_CONTINENTAL`.
- Produces: `ShippingProvider.quote(ShipmentRequest) -> tuple[ShippingQuote, ...]`.
- Produces: `ShippingService.recommend(...) -> ShippingRecommendation`.

- [ ] **Step 1: Write zone and freshness tests**

```python
def test_switzerland_is_non_eu_continental():
    assert classify_country("CH") is ShippingZone.NON_EU_CONTINENTAL

def test_quote_expires_after_24_hours():
    quote = sample_quote(retrieved_at=NOW - timedelta(hours=25))
    assert quote.is_fresh(NOW, timedelta(hours=24)) is False
```

- [ ] **Step 2: Implement exact normalized quote types**

`ShippingQuote` includes provider, service code/name, zone, amount, currency, tracking, insurance, transit range, live-versus-estimate flag, source URLs, assumptions, retrieved time, and expiry time. `ShipmentRequest` requires confirmed packed weight/dimensions, origin postcode, declared value, item restrictions, and destination samples.

- [ ] **Step 3: Implement research and fixed-rate providers**

`ResearchShippingProvider` uses the source-backed research client and accepts only official carrier/aggregator sources with effective dates. It labels results as estimates. `FixedRateProvider` reads seller-confirmed rates from SQLite and labels them publishable. The recommendation ranks tracked services by total cost, then transit time, while preserving every quote for review.

- [ ] **Step 4: Block publication for estimates until seller confirms a fixed buyer-facing rate**

Add `ShippingRecommendation.publishable` and require a selected, fresh, seller-confirmed price for all enabled zones. Non-EU results must include a customs warning.

- [ ] **Step 5: Run shipping tests and commit**

Run: `cd backend && python -m pytest tests/unit/shipping -q`  
Expected: PASS.

```bash
git add backend/app/domain/shipping.py backend/app/integrations/shipping backend/app/application/shipping.py backend/tests/unit/shipping
git commit -m "feat: research European shipping options"
```

## Task 8: Implement eBay OAuth, environments, and account readiness

**Files:**
- Create: `backend/app/integrations/ebay/oauth.py`, `rest.py`, `account.py`, `taxonomy.py`, `metadata.py`
- Create: `backend/app/api/routes/auth.py`
- Test: `backend/tests/unit/ebay/test_oauth.py`, `backend/tests/contract/test_ebay_account.py`

**Interfaces:**
- Produces: `EbayOAuth.begin() -> AuthorizationRequest` and `complete(code, state) -> TokenSet`.
- Produces: `EbayAccountClient.readiness() -> AccountReadiness`.

- [ ] **Step 1: Test state, PKCE, environment separation, and rotation**

```python
def test_callback_rejects_wrong_state(oauth):
    request = oauth.begin()
    with pytest.raises(OAuthStateError):
        oauth.complete(code="auth-code", state=request.state + "changed")

def test_production_token_is_never_used_for_sandbox(token_store):
    token_store.set("production", "prod-token")
    assert token_store.get("sandbox") is None
```

- [ ] **Step 2: Implement loopback OAuth and keychain-backed tokens**

Use cryptographically random state and PKCE verifier, one-time state records with expiry, exact callback matching, atomic refresh-token rotation, and separate keychain names for Sandbox and Production. Request only scopes required by Inventory, Account, Fulfillment, Media, and Trading operations used by this app.

- [ ] **Step 3: Implement account readiness checks**

Read business-policy enrollment, payment/return/fulfillment policies, inventory locations, marketplace `EBAY_IT`, and authorization scopes. Return actionable missing steps; do not create or modify policies automatically.

- [ ] **Step 4: Implement eBay category and requirement validation**

Use Taxonomy category-tree suggestions and Sell Metadata requirements for `EBAY_IT`. Cache responses with provider timestamps and explicit expiry. Given a category and item aspects, return required missing aspects, allowed conditions, regulatory requirements, and unsupported shipping-policy combinations. Preserve unknown enum values as warnings rather than crashing.

- [ ] **Step 5: Run OAuth, account, taxonomy, and metadata contract tests**

Run: `cd backend && python -m pytest tests/unit/ebay/test_oauth.py tests/contract/test_ebay_account.py tests/contract/test_ebay_taxonomy.py tests/contract/test_ebay_metadata.py -q`  
Expected: PASS with all HTTP calls mocked.

- [ ] **Step 6: Commit eBay authentication and metadata**

```bash
git add backend/app/integrations/ebay backend/app/api/routes/auth.py backend/tests/unit/ebay backend/tests/contract
git commit -m "feat: add secure eBay authorization"
```

## Task 9: Upload photos and create unpublished eBay Inventory offers

**Files:**
- Create: `backend/app/integrations/ebay/media.py`, `inventory.py`
- Create: `backend/app/application/drafting.py`
- Test: `backend/tests/contract/test_ebay_media.py`, `test_ebay_inventory.py`
- Test: `backend/tests/unit/application/test_drafting.py`

**Interfaces:**
- Produces: `EbayMediaClient.upload(photo) -> EbayImage`.
- Produces: `EbayInventoryClient.create_draft(payload) -> EbayDraftRef`.

- [ ] **Step 1: Write a draft composer test that preserves defects and target price**

```python
def test_composer_preserves_user_defects_and_target_price(composer, researched_item):
    draft = composer.compose(researched_item)
    assert "scratch on left side" in draft.condition_description.lower()
    assert draft.price == Money("EUR", Decimal("80.00"))
```

- [ ] **Step 2: Implement canonical draft composition and validation**

Compose SKU, title, aspects, condition, condition description, listing description, quantity, `EBAY_IT`, category, target price, policy IDs, merchant location key, selected shipping representation, and regulatory fields. Block missing required fields, unconfirmed dimensions, stale shipping, unresolved dangerous-goods flags, or omitted known defects.
Validate the composed result with the eBay taxonomy/metadata adapters before creating provider resources.

- [ ] **Step 3: Implement Media and Inventory REST adapters**

Upload local images through the supported eBay Media flow, wait for accepted status when required, then call `createOrReplaceInventoryItem` and `createOffer`. Store SKU, media IDs/URLs, offer ID, warnings, and request fingerprint. Never call `publishOffer` in this task.

After `createOffer`, call Inventory `getListingFees` for the unpublished offer when supported and store returned fee estimates with currency, retrieval time, and provider warnings. A missing fee estimate is displayed as unavailable and does not become a fabricated value.

- [ ] **Step 4: Add the Seller Hub limitation acknowledgement**

Before the first Production draft, require a persisted acknowledgement: `Listings created through the Inventory API must be revised through this application/API and cannot currently be edited in Seller Hub.` Sandbox tests may use a fixture acknowledgement.

- [ ] **Step 5: Run draft contract tests and commit**

Run: `cd backend && python -m pytest tests/unit/application/test_drafting.py tests/contract/test_ebay_media.py tests/contract/test_ebay_inventory.py -q`  
Expected: PASS.

```bash
git add backend/app/application/drafting.py backend/app/integrations/ebay/media.py backend/app/integrations/ebay/inventory.py backend/tests
git commit -m "feat: create unpublished eBay offers"
```

## Task 10: Bind approval to canonical payloads and publish idempotently

**Files:**
- Create: `backend/app/application/approval.py`, `publishing.py`
- Create: `backend/app/api/routes/drafts.py`
- Test: `backend/tests/unit/application/test_approval.py`, `test_publishing.py`

**Interfaces:**
- Produces: `canonicalize(draft) -> bytes`, `approve(draft_id) -> Approval`.
- Produces: `PublishingService.publish(approval_id) -> ListingRef`.

- [ ] **Step 1: Test hash stability and invalidation**

```python
def test_material_change_invalidates_approval(approval_service, draft):
    approval = approval_service.approve(draft)
    changed = draft.model_copy(update={"price": Money("EUR", Decimal("81.00"))})
    assert approval_service.matches(approval, changed) is False

def test_key_order_does_not_change_hash():
    assert payload_hash({"a":1,"b":2}) == payload_hash({"b":2,"a":1})
```

- [ ] **Step 2: Implement canonical JSON and SHA-256 approval records**

Normalize decimals as strings, sort object keys, preserve array order, encode UTF-8, exclude non-material display metadata, and store the complete canonical payload alongside its hash. Approval requires no blocking warnings and a fresh shipping confirmation.

- [ ] **Step 3: Implement idempotent publication and reconciliation**

Create operation key `publish:{offer_id}:{draft_hash}` transactionally. Re-fetch the eBay offer, compare material fields, then call `publishOffer`. On timeout or ambiguous response, call `getOffer` and reconcile listing status before permitting retry. Store listing ID and URL exactly once.

- [ ] **Step 4: Test duplicate prevention and ambiguous response recovery**

Run: `cd backend && python -m pytest tests/unit/application/test_approval.py tests/unit/application/test_publishing.py -q`  
Expected: PASS, including a test asserting two publish requests produce one provider mutation.

- [ ] **Step 5: Commit approval and publishing**

```bash
git add backend/app/application/approval.py backend/app/application/publishing.py backend/app/api/routes/drafts.py backend/tests/unit/application
git commit -m "feat: publish only approved draft versions"
```

## Task 11: Add listing revisions, withdrawal, and read-only activity notifications

**Files:**
- Create: `backend/app/application/listing_management.py`
- Create: `backend/app/application/activity.py`
- Create: `backend/app/integrations/ebay/fulfillment.py`, `trading.py`
- Create: `backend/app/api/routes/activity.py`
- Test: `backend/tests/unit/application/test_activity.py`, `backend/tests/contract/test_ebay_activity.py`
- Test: `backend/tests/unit/application/test_listing_management.py`

**Interfaces:**
- Produces: `ActivityService.refresh(trigger: STARTUP|LISTING_MUTATION) -> RefreshSummary`.
- Produces: normalized `OFFER`, `SALE`, and `REFUND` events.
- Produces: `ListingManagementService.propose_revision`, `apply_approved_revision`, and `withdraw_approved_listing`.

- [ ] **Step 1: Test event deduplication and trigger rules**

```python
async def test_same_offer_status_alerts_once(activity_service, offer_source):
    offer_source.events = [offer_event("offer-1", "ACTIVE")]
    first = await activity_service.refresh(RefreshTrigger.STARTUP)
    second = await activity_service.refresh(RefreshTrigger.STARTUP)
    assert first.created == 1
    assert second.created == 0

async def test_changed_refund_status_creates_new_alert(activity_service, order_source):
    order_source.events = [refund_event("refund-1", "PENDING")]
    await activity_service.refresh(RefreshTrigger.STARTUP)
    order_source.events = [refund_event("refund-1", "COMPLETED")]
    assert (await activity_service.refresh(RefreshTrigger.LISTING_MUTATION)).created == 1
```

- [ ] **Step 2: Implement approval-bound revisions and withdrawal**

`propose_revision` creates a new canonical draft version and invalidates any prior approval. `apply_approved_revision` re-fetches the offer, verifies the approved hash, and calls `updateOffer` with the complete required offer payload. `withdraw_approved_listing` requires a separate canonical action summary and calls `withdrawOffer`, retaining the unpublished offer. Both use operation keys and reconciliation rules equivalent to publication, then trigger one activity refresh.

Add tests asserting a price edit cannot call `updateOffer` before reapproval, and two withdrawal requests result in at most one provider mutation.

- [ ] **Step 3: Implement read-only eBay activity adapters**

Use Trading `GetBestOffers` for active buyer offers and counters. Use Fulfillment `getOrders` with modification windows for completed-checkout sales and payment-summary refund status. Parse only required fields, tolerate unknown enum values, minimize buyer data, and never expose write methods from these adapters.

- [ ] **Step 4: Implement checkpoints and partial-failure behavior**

Deduplication key is `{event_type}:{provider_id}:{material_status_or_revision}`. Advance a source checkpoint only after all pages for its requested window succeed. Return successful events plus source-specific errors when another source fails.

- [ ] **Step 5: Trigger refresh after successful listing mutations**

Call `ActivityService.refresh(LISTING_MUTATION)` after publish, updateOffer, and withdrawOffer complete. In FastAPI lifespan startup, enqueue one `STARTUP_ACTIVITY_REFRESH` job after the database is ready and authorization is valid; do not add a timer.

- [ ] **Step 6: Run listing-management and activity tests and commit**

Run: `cd backend && python -m pytest tests/unit/application/test_listing_management.py tests/unit/application/test_activity.py tests/contract/test_ebay_activity.py -q`  
Expected: PASS.

```bash
git add backend/app/application/listing_management.py backend/app/application/activity.py backend/app/integrations/ebay/fulfillment.py backend/app/integrations/ebay/trading.py backend/app/api/routes/activity.py backend/tests
git commit -m "feat: notify once for offers sales and refunds"
```

## Task 12: Add manual tracking entry and login-triggered carrier status refresh

**Files:**
- Create: `backend/app/domain/tracking.py`
- Create: `backend/app/integrations/tracking/base.py`, `carrier_adapter.py`
- Create: `backend/app/application/tracking.py`
- Create: `backend/app/api/routes/tracking.py`
- Test: `backend/tests/unit/domain/test_tracking.py`, `backend/tests/unit/application/test_tracking.py`
- Test: `backend/tests/contract/test_tracking_adapter.py`

**Interfaces:**
- Produces: `TrackingService.add(direction: OUTBOUND|INBOUND, carrier, tracking_number, label, item_id: str | None = None) -> TrackingRecord`.
- Produces: `TrackingService.refresh(trigger: LOGIN|MANUAL, record_id: str | None = None) -> TrackingRefreshSummary`.
- Produces: normalized `TrackingStatus` (`INFO_RECEIVED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`, `UNKNOWN`) and `TrackingCheckpoint` (description, location, provider timestamp).
- Consumes: `TrackingProvider.lookup(carrier, tracking_number) -> TrackingSnapshot` behind a narrow adapter interface with no eBay or shipping-quote dependencies.

- [ ] **Step 1: Test status normalization, delivered-record exclusion, and both directions**

```python
async def test_delivered_record_excluded_from_login_refresh(tracking_service, provider):
    record = await tracking_service.add(direction="OUTBOUND", carrier="dhl", tracking_number="JD0001", label="Sold: lens", item_id="item-1")
    provider.snapshots[record.id] = tracking_snapshot(status="DELIVERED")
    await tracking_service.refresh(RefreshTrigger.LOGIN)

    provider.snapshots[record.id] = tracking_snapshot(status="EXCEPTION")
    summary = await tracking_service.refresh(RefreshTrigger.LOGIN)
    assert summary.checked == 0  # delivered record skipped automatically

async def test_manual_refresh_still_reaches_delivered_record(tracking_service, provider):
    record = await tracking_service.add(direction="OUTBOUND", carrier="dhl", tracking_number="JD0001", label="Sold: lens", item_id="item-1")
    provider.snapshots[record.id] = tracking_snapshot(status="DELIVERED")
    await tracking_service.refresh(RefreshTrigger.LOGIN)

    summary = await tracking_service.refresh(RefreshTrigger.MANUAL, record_id=record.id)
    assert summary.checked == 1

async def test_inbound_record_requires_no_item_link(tracking_service):
    record = await tracking_service.add(direction="INBOUND", carrier="ups", tracking_number="1Z999", label="Replacement battery")
    assert record.item_id is None
    assert record.direction == "INBOUND"
```

- [ ] **Step 2: Implement the tracking domain and manual entry**

`TrackingRecord` requires `direction` (`OUTBOUND`/`INBOUND`), `carrier`, `tracking_number`, `label`, creation timestamp, and an optional `item_id`; it starts with status `UNKNOWN` and no checkpoints until the first refresh. `item_id` is only meaningful for `OUTBOUND` records and, when present, must reference a local item already in state `LIVE` or later. `INBOUND` records never carry an `item_id` and have no relationship to any listing, order, or eBay data. Persist records and their latest snapshot in SQLite.

- [ ] **Step 3: Implement the provider-neutral carrier tracking adapter**

Define `TrackingProvider` as a narrow interface parsed into `TrackingSnapshot` (status, checkpoints, last update time). Implement one adapter against a chosen tracking API/aggregator (see deferred decision in the design spec) plus a deterministic fixture provider for tests. Adapter failures raise a normalized `TrackingLookupError` and never raise raw provider exceptions to the application layer.

- [ ] **Step 4: Implement login and on-demand refresh**

`TrackingService.refresh(LOGIN)` queries every record whose last known status is not `DELIVERED`, updates status/checkpoints on success, and leaves the last known good status untouched on a per-record adapter failure. Refresh never runs on a timer. Enqueue one `LOGIN_TRACKING_REFRESH` job after authentication succeeds, alongside the existing startup activity refresh. `refresh(MANUAL, record_id=...)` refreshes exactly one record regardless of its current status.

- [ ] **Step 5: Add the tracking API route**

Expose `POST /api/tracking` to add a record (direction, carrier, tracking number, label, and optional item_id), `GET /api/tracking` to list all records across both directions, and `POST /api/tracking/{record_id}/refresh` for on-demand refresh; all require the same auth as other routes. Never expose a route that writes tracking data to eBay.

- [ ] **Step 6: Run tracking tests and commit**

Run: `cd backend && python -m pytest tests/unit/domain/test_tracking.py tests/unit/application/test_tracking.py tests/contract/test_tracking_adapter.py -q`  
Expected: PASS.

```bash
git add backend/app/domain/tracking.py backend/app/integrations/tracking backend/app/application/tracking.py backend/app/api/routes/tracking.py backend/tests
git commit -m "feat: add manual tracking entry and login status refresh"
```

## Task 13: Build the review, approval, listing, and notification interface

**Files:**
- Create: `frontend/src/api/client.ts`, `frontend/src/app/router.tsx`
- Create: `frontend/src/features/research/ResearchEvidence.tsx`
- Create: `frontend/src/features/review/DraftReview.tsx`, `ApprovalSummary.tsx`
- Create: `frontend/src/features/listings/ListingDashboard.tsx`
- Create: `frontend/src/features/activity/NotificationCenter.tsx`
- Create: `frontend/src/features/tracking/TrackingList.tsx`
- Test: matching `*.test.tsx` files.

**Interfaces:**
- Consumes: typed `/api/items`, `/research`, `/drafts`, `/activity`, `/tracking`, and `/auth` responses.

- [ ] **Step 1: Test that review exposes defects, uncertainty, shipping, and price differences**

```tsx
it("shows every consequential field before approval", () => {
  render(<DraftReview draft={draftFixture} />);
  expect(screen.getByText(/scratch on left side/i)).toBeVisible();
  expect(screen.getByText(/inferred/i)).toBeVisible();
  expect(screen.getByText(/target €80.00/i)).toBeVisible();
  expect(screen.getByText(/non-eu customs/i)).toBeVisible();
});
```

- [ ] **Step 2: Implement the typed API client and route-level loading/error states**

Generate or hand-maintain narrow TypeScript response types from backend schemas. Never render raw provider errors. Cancel stale requests when navigating away.

- [ ] **Step 3: Implement review and explicit approval UI**

Show photos, title, category, aspects, condition/defects, sources, provenance, target versus recommended price, fees, shipping by zone, customs warnings, policies, unresolved questions, and eBay warnings. Approval button text is `Approve this exact draft`; it is disabled when the draft is stale or blocked. Editing after approval visibly clears approval.

- [ ] **Step 4: Implement listing dashboard and notification center**

Show local/eBay state, last synchronization, listing URL, and proposed revision actions. Notification cards show event type, listing title, amount/currency, status, and time; exclude buyer address/email/payment data. Marking read changes only local state.

Implement `TrackingList` as a standalone view (not nested under a single item) showing direction, label, linked item (if any), carrier, tracking number, current status, last checkpoint, last successful refresh time, and a link to the carrier's own tracking page. Include an "Add tracking number" form that lets the seller choose outbound (optionally linked to one of their items) or inbound (no item link), and a per-row "Refresh now" action.

- [ ] **Step 5: Run frontend tests and accessibility checks**

Run: `cd frontend && npm test -- --run && npm run lint && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 6: Commit the interface**

```bash
git add frontend/src frontend/tests
git commit -m "feat: add listing review and activity interface"
```

## Task 14: Add end-to-end tests, protected Sandbox workflow, and production-call guard

**Files:**
- Create: `frontend/tests/e2e/listing-flow.spec.ts`
- Create: `backend/tests/e2e/test_sandbox_publish.py`
- Create: `scripts/verify_no_production_calls.py`
- Create: `.github/workflows/sandbox-e2e.yml`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: repeatable mocked local E2E flow and protected real Sandbox smoke test.

- [ ] **Step 1: Add mocked browser E2E coverage**

Note: Task 13 delivered the review/listings/activity/tracking screens as
components wired individually (a dumb `DraftReview` fed by props, a
`TrackingContainer` fetching `/api/tracking`), not a single connected
per-item pipeline UI (intake → research trigger → shipping confirmation →
draft → approve → publish) driven by real navigation between those steps.
Building that orchestration is a larger frontend feature than Task 13's
component-by-component scope covered, so the full "intake → ... → publish"
browser E2E described here is deferred until that pipeline UI exists.
Instead, this step covers real, currently-wired flows end-to-end in a
browser: submitting the intake form, and adding an outbound (linked to an
item) and an inbound (no item link) tracking number, then confirming a
simulated login refresh updates both records' status.

Run: `cd frontend && npx playwright test tests/e2e/listing-flow.spec.ts`  
Expected: PASS using mocked backend responses (`page.route`).

- [ ] **Step 2: Add Sandbox publication smoke test**

The test creates a fictional low-value Sandbox inventory item, uploads a generated fixture image, creates an unpublished offer, approves the hash, publishes once, verifies listing ID, then withdraws the Sandbox offer in cleanup. Skip unless `RUN_EBAY_SANDBOX_E2E=1` and required Sandbox secrets are injected.

- [ ] **Step 3: Add the production-call guard**

`scripts/verify_no_production_calls.py` must fail credentialed tests if any configured URL is outside the exact eBay Sandbox host allowlist. Run it before and after Sandbox tests and inspect recorded HTTP destinations.

- [ ] **Step 4: Add protected manual GitHub workflow**

Configure `workflow_dispatch`, a protected `ebay-sandbox` environment, read-only repository permissions, no fork execution, concurrency `ebay-sandbox`, secret-masked output, production-call guard, and no uploaded provider payload artifacts. Pin actions to full SHAs during implementation.

- [ ] **Step 5: Run complete credential-free verification**

Run: `cd backend && python -m ruff check . && python -m mypy app && python -m pytest -m "not sandbox" -q`  
Run: `cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build && npx playwright test`  
Run: `python scripts/check_no_secrets.py`  
Expected: all PASS.

- [ ] **Step 6: Commit E2E and workflows**

```bash
git add .github frontend/tests/e2e backend/tests/e2e scripts
git commit -m "ci: verify listing workflow and sandbox publishing"
```

## Task 15: Complete documentation, privacy checks, and public-repository readiness

**Files:**
- Modify: `README.md`, `AGENTS.md`
- Create: `SECURITY.md`, `CONTRIBUTING.md`, `LICENSE`, `docs/architecture.md`, `docs/setup.md`, `docs/privacy.md`
- Create: fictional sample configuration and sample listing fixtures.

**Interfaces:**
- Produces: reproducible local setup and safe public release package.

- [ ] **Step 1: Document setup and external requirements**

Explain Python/Node requirements, local startup, eBay developer account approval, Sandbox/Production separation, business policies, inventory location, OpenAI API configuration and possible costs, shipping-rate confirmation, OAuth scopes, and OS-keychain behavior. State the Inventory API Seller Hub limitation prominently.

- [ ] **Step 2: Document the approval and notification safety model**

Explain canonical draft hashes, reapproval after material changes, idempotent publish, read-only notifications, manual tracking entry and login-triggered status refresh, trigger timing, no continuous polling, data retention, local deletion/export, and incident response.

- [ ] **Step 3: Add public repository governance**

Add MIT license text, contribution workflow, private vulnerability-reporting instructions, supported versions, and the public-release sensitive-data checklist from `AGENTS.md`.

- [ ] **Step 4: Perform clean-checkout verification**

Run from a fresh temporary clone:

```bash
python scripts/check_no_secrets.py
cd backend && python -m ruff check . && python -m mypy app && python -m pytest -m "not sandbox" -q
cd ../frontend && npm ci && npm run lint && npm run typecheck && npm test -- --run && npm run build && npx playwright test
```

Expected: all checks PASS with no credentials and no network-dependent tests.

- [ ] **Step 5: Review Git history before publication**

Run two independent secret scanners, search the full Git history for provider key patterns, emails, addresses, bearer tokens, private keys, SQLite headers, and image files, then inspect screenshots and workflow artifacts manually. Revoke any credential before cleaning history if exposure is detected.

- [ ] **Step 6: Commit documentation**

```bash
git add README.md AGENTS.md SECURITY.md CONTRIBUTING.md LICENSE docs examples
git commit -m "docs: prepare listing copilot for public reference"
```

## Final acceptance gate

- [ ] All credential-free CI checks pass from a clean checkout.
- [ ] Protected Sandbox workflow publishes and withdraws exactly one fictional test listing.
- [ ] A changed approved payload requires reapproval.
- [ ] Repeated publish requests cannot create duplicate listings.
- [ ] Known defects appear in the final eBay payload.
- [ ] Shipping publication is blocked without confirmed dimensions and fresh selected rates for enabled zones.
- [ ] Offer, sale, and refund events alert once per material status and never trigger writes.
- [ ] A manually entered tracking number shows a normalized status after login refresh, without any write to eBay or the carrier.
- [ ] Logs, notifications, fixtures, artifacts, and Git history contain no credentials or personal seller/buyer data.
- [ ] The owner reviews the exact repository contents before making it public.

## Official references to verify during implementation

- [eBay Inventory API overview](https://developer.ebay.com/api-docs/sell/inventory/static/overview.html)
- [Managing eBay offers](https://developer.ebay.com/api-docs/sell/static/inventory/managing-offers.html)
- [eBay Account API overview](https://developer.ebay.com/api-docs/sell/account/static/overview.html)
- [eBay Fulfillment API](https://developer.ebay.com/develop/api/sell/fulfillment_api)
- [eBay Trading `GetBestOffers`](https://developer.ebay.com/devzone/xml/docs/reference/ebay/GetBestOffers.html)
- [eBay shipping rate tables](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/shipping-rate-tables.html)
- Current official OpenAI Responses API multimodal and web-search documentation before implementing the live research adapter.
