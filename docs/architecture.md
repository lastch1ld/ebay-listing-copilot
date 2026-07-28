# Architecture

The full design rationale lives in
[`docs/superpowers/specs/2026-07-17-ebay-listing-copilot-design.md`](superpowers/specs/2026-07-17-ebay-listing-copilot-design.md).
This page is a shorter map of the codebase for people reading the code, not
the design history.

## Stack

- **Backend:** FastAPI + Pydantic 2 + SQLAlchemy 2 + Alembic, on Python 3.12.
- **Frontend:** React + TypeScript + Vite, tested with Vitest and Playwright.
- **Storage:** SQLite (`backend/data/app.db`, gitignored).
- **Secrets:** OS keychain via `keyring`, never `.env` for long-lived tokens.

## Backend layout

```text
backend/app/
├── main.py                  # FastAPI app assembly and dependency wiring
├── config.py                 # Settings (env-driven), Environment enum
├── domain/                   # Pure types: Money, provenance, state machine,
│                              #   shipping zones/quotes, draft, tracking
├── application/               # Use-case services (no provider SDK imports):
│                              #   intake, research, shipping, drafting,
│                              #   approval, publishing, listing_management,
│                              #   activity, tracking, jobs
├── integrations/
│   ├── ebay/                 # oauth, rest, inventory, media, account,
│   │                          #   taxonomy, metadata, fulfillment, trading
│   ├── openai/                # research.py (OpenAI Responses adapter)
│   ├── shipping/              # research + fixed-rate providers
│   └── tracking/              # carrier tracking adapter
├── persistence/               # SQLAlchemy models + repositories
├── security/                  # secrets (keyring wrapper), redaction
└── api/routes/                 # thin FastAPI routers per feature
```

The dependency direction is one-way: `api/routes` → `application` →
`domain` + `persistence`, with `integrations/*` implementing narrow
interfaces defined in `application/*` or `integrations/*/base.py`. Nothing in
`domain/` imports an eBay, OpenAI, shipping, or tracking SDK type.

## Frontend layout

```text
frontend/src/
├── app/
│   ├── App.tsx      # environment banner + router mount
│   └── router.tsx    # tab-based navigation, container components
├── api/               # typed fetch client (client.ts) + response types
└── features/
    ├── intake/        # ItemIntakeForm
    ├── research/       # ResearchEvidence
    ├── review/         # DraftReview, ApprovalSummary
    ├── listings/        # ListingDashboard
    ├── activity/        # NotificationCenter
    └── tracking/         # TrackingList
```

Feature components are written as "dumb" components driven by props/callbacks
where practical, with small container components in `router.tsx` doing data
fetching. There is no client-side router library — this is a local,
single-user control panel, not a multi-page public site.

## Key workflows

- **Approval → publish:** `application/approval.py` canonicalizes a draft to
  a stable JSON payload and SHA-256 hash; `application/publishing.py` binds
  publication to that exact hash via an idempotent `OperationRepository` key
  (`publish:{offer_id}:{draft_hash}`), so a repeated request never creates a
  second listing.
- **Background jobs:** `application/jobs.py`'s `JobRunner` leases jobs with an
  expiry, so a crash mid-job is resumed by the next runner instead of losing
  the work or double-processing it.
- **Activity / tracking refresh:** both are trigger-based only (login/startup
  and after a listing mutation, or on-demand for a single tracking record) —
  never a background poller. See `docs/privacy.md` for what that means for
  data retention.

## Where to look for a given feature

| Feature | Domain | Application | Integration |
|---|---|---|---|
| Item intake | `domain/common.py` | `application/intake.py` | — |
| Research | — | `application/research.py` | `integrations/openai/research.py` |
| Shipping | `domain/shipping.py` | `application/shipping.py` | `integrations/shipping/*` |
| Draft composition | `domain/draft.py` | `application/drafting.py` | — |
| Approval / publish | — | `application/approval.py`, `publishing.py` | `integrations/ebay/inventory.py` |
| Revisions / withdrawal | — | `application/listing_management.py` | `integrations/ebay/inventory.py` |
| Activity notifications | — | `application/activity.py` | `integrations/ebay/trading.py`, `fulfillment.py` |
| Package tracking | `domain/tracking.py` | `application/tracking.py` | `integrations/tracking/*` |
