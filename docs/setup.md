# Setup

## Requirements

- Python 3.12+
- Node.js 22+
- An eBay developer account, approved for the Sandbox and (later) Production
  environments at [developer.ebay.com](https://developer.ebay.com)
- Optionally, an OpenAI API key if you want live, source-backed item research
  instead of the built-in "not configured" placeholder
- Optionally, a multi-carrier tracking API/aggregator account if you want live
  package-tracking status instead of the built-in placeholder

## Local install

```bash
cd backend
python -m pip install --editable ".[dev]"
python -m alembic upgrade head

cd ../frontend
npm ci
```

## Configuration

Copy `.env.example` to `.env` at the repository root and fill in the values
you need. Every value in `.env.example` is a name/description only — never
commit real values (`.env` is gitignored).

- `EBAY_ENVIRONMENT`: `sandbox` while developing; switch to `production` only
  once you are ready to publish real listings.
- `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET`: from your eBay developer
  application, matching the environment above. Sandbox and Production use
  **different** keysets — do not mix them.
- `EBAY_REDIRECT_URI`: must exactly match a redirect URI configured on your
  eBay application; the default assumes the backend runs on
  `127.0.0.1:8000`.
- `OPENAI_API_KEY` / `OPENAI_MODEL`: required only for live item research.
  Using OpenAI's API has a cost per request; without these set, research
  requests fail cleanly with a "not configured" error instead of running.
- `TRACKING_PROVIDER_BASE_URL`: required only for live carrier tracking
  lookups. Without it, tracking lookups fail cleanly with a "not configured"
  error; you can still add tracking numbers manually.
- `DATABASE_URL`: local SQLite path; the default is fine for normal use.

Long-lived secrets (OAuth refresh tokens) are never kept in `.env` — they are
written to your OS keychain via the `keyring` library once you complete the
eBay OAuth flow.

## eBay account readiness

Before creating a listing, your eBay Sandbox or Production seller account
needs, for the `EBAY_IT` marketplace:

- A payment policy
- A return policy
- A fulfillment (shipping) policy
- At least one inventory location

The app's account-readiness check (`EbayAccountClient.readiness()`) reports
which of these are missing; it never creates or modifies policies for you.

## Important limitation: Seller Hub

Listings created through the eBay Inventory API (which this app uses) **must
be revised through this application**, not Seller Hub — Seller Hub currently
does not support editing Inventory API listings directly. The app requires an
explicit acknowledgement of this before the first Production draft.

## Shipping rates

The first release covers Italy (domestic), EU continental Europe, and
non-EU continental Europe (e.g. Switzerland, Norway) as separate zones.
Researched shipping quotes are always labeled as estimates and cannot be
published; you must confirm a seller-set fixed rate for each zone before a
listing becomes publishable.

## Running locally

```bash
# backend
cd backend
python -m uvicorn app.main:app --reload

# frontend, in another terminal
cd frontend
npm run dev
```

The backend binds to `127.0.0.1` only by default — it is not exposed to your
LAN or the internet.

## Running the test suites

```bash
cd backend && python -m pytest -m "not sandbox" -q
cd ../frontend && npm test -- --run && npx playwright test
```

The real eBay Sandbox smoke test (`backend/tests/e2e/test_sandbox_publish.py`)
only runs when `RUN_EBAY_SANDBOX_E2E=1` and the Sandbox credential
environment variables it requires are set — see that file for the exact list.
It is also available as the manually-dispatched, protected `sandbox-e2e`
GitHub Actions workflow.
