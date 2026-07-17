# eBay Listing Copilot — Design Specification

**Date:** 2026-07-17  
**Status:** Approved; implementation plan created
**Intended license:** MIT  

## 1. Purpose

eBay Listing Copilot is a local web application that helps one seller create and manage their own eBay listings with minimal input. The seller provides item photos, a brief description, known defects, and a target price. The application researches the item, comparable listings, and shipping options; prepares a complete unpublished eBay draft; summarizes the evidence and proposed terms; and publishes only after the seller explicitly approves the exact draft.

The project is intended to become a public GitHub reference repository. All real credentials, tokens, seller identifiers, inventory records, photos, and operational logs remain outside version control.

## 2. Goals

- Reduce repetitive data entry while keeping the seller in control.
- Produce complete, accurate, and policy-aware listing drafts from limited user input.
- Preserve and prominently disclose known defects.
- Research product details and pricing with visible sources and uncertainty labels.
- Research shipping within Italy and across continental Europe, including non-EU destinations.
- Surface new offers, completed sales, and refunds through deduplicated, read-only notifications.
- Bind approval to an immutable draft version so an approved listing cannot change silently before publication.
- Provide a modular, testable codebase that is safe to publish.

## 3. Non-goals for the first release

- Autonomous publication without seller approval.
- Automatic price changes, relisting, or ending of live listings.
- Automatic offer acceptance, countering, rejection, or refund issuance.
- Order fulfillment, shipment purchase, tracking upload, customer messaging, returns, or accounting.
- Bulk multi-seller or marketplace-as-a-service operation.
- Guaranteed item identification from images alone.
- Legal, tax, customs, authenticity, or appraisal guarantees.
- Scraping websites in violation of their terms or bypassing access controls.

## 4. User workflow

### 4.1 Intake

The seller creates an item workspace and supplies:

- One or more item photos
- A short description
- All known damage, missing parts, modifications, or authenticity concerns
- A target price and currency
- Package weight and dimensions, confirmed before shipping is finalized

The seller's ship-from country and postcode, preferred handling time, return policy, packaging allowance, and default excluded destinations are saved as local settings and reused.

### 4.2 Research

The application analyzes the supplied information and performs bounded research. It gathers:

- Likely manufacturer, product name, model, variant, era, and identifiers
- Authoritative product specifications where available
- Suitable eBay category and required item specifics
- Comparable eBay listings and other relevant market evidence
- Shipping services and prices for the configured destination zones
- Potential policy, condition, authenticity, dangerous-goods, customs, or restricted-item concerns

Every researched field records a provenance classification:

- `USER_PROVIDED`: stated directly by the seller
- `OBSERVED`: visible in supplied photos
- `SOURCE_VERIFIED`: supported by a cited external source
- `INFERRED`: plausible but not verified
- `UNKNOWN`: missing and not safely inferable

Inferred and unknown values are never silently converted into facts.

### 4.3 Draft generation

The application proposes:

- eBay marketplace and category
- SEO-conscious title within eBay's current constraints
- Condition and condition description
- Required and recommended item specifics
- Plain, accurate listing description
- Quantity and SKU
- Seller's target price and a separately displayed research-based recommendation
- Return, payment, and fulfillment-policy references
- Domestic and international shipping services and buyer-facing prices
- Destination exclusions and customs warnings

The seller's target price remains the draft price unless the seller explicitly selects a different recommendation.

### 4.4 Validation and eBay draft

Before contacting eBay, the application validates required fields, category-specific requirements, policy references, image availability, price, quantity, package information, and shipping coverage.

It then creates or updates an unpublished eBay draft. The application retrieves the resulting eBay validation messages and incorporates warnings or errors into the review screen. A draft with blocking errors cannot be approved.

### 4.5 Approval summary

The review screen shows:

- Photos and proposed title
- Category and all material item specifics
- Condition, defects, and missing parts
- Target price, recommended price, and supporting comparisons
- Shipping options for Italy, EU continental Europe, and non-EU continental Europe
- Handling time, returns, destination exclusions, and customs implications
- Estimated eBay fees when eBay provides a usable estimate
- Source links, retrieval timestamps, and confidence labels
- Missing information, policy warnings, and unresolved assumptions

The seller may approve, reject, or request changes. Approval records the exact normalized draft payload, its cryptographic hash, the user action, and the timestamp. Any subsequent change invalidates approval and requires a new review.

### 4.6 Publication

After approval, the application verifies that:

- The draft version still matches the approved hash.
- Required eBay policies and seller authorization remain valid.
- Shipping quotes and research have not exceeded their configured freshness limits.
- eBay has not introduced new validation errors.

The application then publishes the offer once, using an idempotent operation record to prevent duplicate listings. On success it stores and displays the live listing ID, URL, publication timestamp, and final payload. If the outcome is ambiguous, it reconciles with eBay before allowing another publish attempt.

### 4.7 Listing management

The application can import and display its managed drafts and live listings. It may propose revisions to price, quantity, content, policies, or shipping, but material changes follow the same versioned review-and-approval workflow. Relisting and ending a listing also require explicit approval and a clear impact summary.

### 4.8 Activity notifications

The application provides a local notification center for:

- New or materially changed buyer Best Offers and counteroffers
- Newly completed sales after checkout and cleared payment
- Newly observed refund activity or refund-status changes

Activity refresh is deliberately trigger-based in the first release:

1. Run once after the application finishes loading and seller authorization is available.
2. Run once after a successful publish, revise, relist, or end operation.
3. Do not poll continuously in the background.

The refresh queries eBay for changes since the last successful activity checkpoint. Best Offers are retrieved through the Trading API `GetBestOffers` capability. Completed sales and refund status are read from Fulfillment orders and their payment summaries. The implementation must tolerate API capability or marketplace differences and report a partial refresh rather than hiding successful results.

Each normalized activity record contains a provider event or entity identifier, event type, relevant listing and order identifiers, provider status or revision, provider timestamp, first-seen timestamp, and local read state. A deduplication key combines the stable provider identifier with the status or revision that represents a material change. An unchanged record is not shown as a new alert on every launch.

Notifications show only the minimum seller-relevant information: listing title, event type, amount and currency when applicable, status, time, and a link to the local detail view or eBay. Buyer addresses, email addresses, payment details, and raw provider payloads are excluded from notification previews.

This feature is read-only. Refreshing notifications never accepts, counters, or declines an offer and never issues a refund. Those actions are outside the first release and would require a separate approval-bound design.

## 5. Shipping design

### 5.1 Scope

The shipping engine supports:

- Italy as the domestic zone
- EU continental-European destinations
- Non-EU continental-European destinations such as Switzerland and Norway

EU and non-EU destinations remain separate because customs declarations, duties, taxes, carrier availability, transit times, and prohibited-item rules differ. Islands and remote territories are not assumed to share mainland rates; they can be excluded or assigned dedicated zones.

### 5.2 Inputs

Shipping research requires:

- Ship-from country and postcode
- Destination country or representative postcode for each zone
- Packed weight and dimensions
- Declared value
- Item type and dangerous-goods indicators
- Tracking and insurance preferences
- Packaging/handling allowance

The application may estimate package data to reduce effort, but publication is blocked until the seller confirms weight and dimensions.

### 5.3 Quote sources

Shipping is implemented behind a provider-neutral interface. Adapters may use:

- Authorized carrier or shipping-aggregator APIs for live quotes
- Seller-specific contracted rate tables
- Public carrier price documents for clearly labeled research estimates
- Manually maintained fallback tables with effective dates

Each quote stores the provider, service, amount, currency, transit estimate, tracking and insurance attributes, destination assumptions, retrieval time, and whether the quote is live or estimated. The system never represents a public-page estimate as a guaranteed purchasable rate.

### 5.4 eBay representation

For eBay Italy, the application does not rely on native calculated shipping. It converts approved quotes into eBay-compatible fulfillment policies, flat shipping costs, or domestic/international shipping-rate tables. The selected mapping and any rounding or packaging allowance are visible in the approval summary.

### 5.5 Freshness and failures

Shipping quote freshness is configurable; the initial safe default is 24 hours. Expired or unavailable quotes block publication until refreshed or explicitly replaced with a seller-entered fixed price. Partial carrier failure does not erase successful quotes, but the summary identifies unavailable providers.

## 6. Architecture

The application runs locally and binds only to the loopback interface by default.

### 6.1 Components

1. **Web interface** — item intake, research progress, draft editing, evidence display, approval, publication status, and listing management.
2. **Application API** — coordinates workflows and enforces state transitions and approval rules.
3. **Research service** — orchestrates image/text analysis, web research, source capture, field provenance, and comparable-listing analysis.
4. **Draft composer** — creates normalized listing proposals without depending directly on eBay transport details.
5. **eBay adapter** — handles OAuth, account capabilities, policies, taxonomy, draft creation, validation, publication, revision, and reconciliation.
6. **Shipping engine** — normalizes quotes from replaceable provider adapters and maps approved rates to eBay shipping policies.
7. **Approval service** — versions normalized drafts, computes hashes, records approvals, and invalidates stale approvals.
8. **Local persistence** — stores settings, item records, research evidence, draft versions, approvals, operation logs, and eBay identifiers.
9. **Background job runner** — executes bounded research, quote collection, image processing, and eBay synchronization with retry rules.
10. **Activity monitor** — performs trigger-based offer, sale, and refund refreshes; normalizes provider records; advances checkpoints; and creates deduplicated local notifications.

### 6.2 Dependency boundaries

- The domain model does not import eBay, AI-provider, search-provider, or shipping-provider SDK types.
- External integrations implement narrow interfaces and translate into internal normalized records.
- Draft generation is testable with fixed evidence and no network access.
- Publication requires an approval record from the approval service; the web interface cannot bypass this rule.
- Provider-specific failures remain inside their adapters and surface as normalized actionable errors.
- Activity refresh is read-only and cannot invoke offer-response or refund-write operations.

### 6.3 Suggested implementation shape

The implementation plan should select a maintainable local-web stack with:

- A typed web frontend
- A small local application API
- SQLite for structured local data
- A local filesystem area for photos and generated artifacts
- Background jobs that survive application restarts
- An AI-provider interface capable of image analysis and source-backed web research
- A system-keychain or equivalent local secret store where practical

Exact libraries and model identifiers will be chosen during implementation planning using current official documentation.

## 7. State model

An item progresses through explicit states:

`INTAKE` → `RESEARCHING` → `NEEDS_INPUT` or `DRAFTING` → `DRAFT_READY` → `EBAY_DRAFTED` → `AWAITING_APPROVAL` → `APPROVED` → `PUBLISHING` → `LIVE`

Recoverable failures enter `ACTION_REQUIRED`; nonrecoverable failures enter `FAILED`. Changes after approval return the item to `AWAITING_APPROVAL`. State transitions are validated server-side and recorded in an audit log.

## 8. Data and privacy

- OAuth tokens, API keys, seller identifiers, real inventory, photos, and logs are excluded from Git.
- `.env.example` contains names and descriptions only, never real values.
- Local databases and upload directories are ignored by default.
- Logs redact authorization headers, tokens, email addresses, addresses, and raw API payload fields known to contain personal data.
- Research sources are stored as URLs, short notes, timestamps, and extracted factual claims rather than copied full pages.
- The application provides local export and deletion controls for seller data.
- Public examples use fictional products and accounts.

## 9. Error handling and recovery

- Network operations use bounded retries with backoff only for retryable failures.
- Validation and authentication failures are not retried blindly.
- Draft and publish operations use idempotency records and reconciliation checks.
- An ambiguous publish response triggers an eBay lookup before any retry.
- Expired OAuth authorization pauses external actions without deleting local work.
- Missing required facts, unresolved defects, stale shipping quotes, or changed drafts block publication.
- Errors shown to the seller explain what failed, what remains safe, and the next action.
- Research and quote jobs retain partial successful results and may be resumed.
- Activity checkpoints advance only after the corresponding provider page or time window has been processed successfully.
- A partial activity refresh records which event sources failed and preserves successful offer, sale, or refund notifications.

## 10. Testing strategy

### 10.1 Unit tests

- Field provenance and confidence handling
- Title and description constraints
- Defect preservation
- Price recommendation separation from target price
- Shipping-zone and customs classification
- Quote normalization and freshness
- Draft hashing and approval invalidation
- State-transition rules and redaction
- Activity deduplication keys, read state, and checkpoint advancement

### 10.2 Integration tests

- eBay adapter against recorded contract fixtures and eBay Sandbox when credentials are available
- Shipping adapters against provider sandboxes or deterministic fixtures
- Research provider with fixed responses and citation records
- OAuth callback and token-refresh flows without exposing secrets
- Local persistence and restart recovery
- Trading `GetBestOffers` and Fulfillment order/refund activity normalization

### 10.3 End-to-end tests

- Intake through unpublished eBay draft
- Approval and successful publication in Sandbox
- Edit-after-approval requiring reapproval
- Ambiguous publish reconciliation preventing duplicates
- Stale shipping quote blocking publication
- Non-EU destination showing customs warnings
- Authentication expiry and recovery
- Startup activity refresh creating each new offer, sale, or refund alert once
- Post-listing-change refresh without continuous polling
- Partial activity-source failure preserving successful notifications

No production listing is used as an automated test target.

## 11. Public repository requirements

The repository will include:

- A concise README and architecture documentation
- Mandatory engineering and credential rules in `AGENTS.md`
- Safe setup instructions and sample configuration
- Fictional sample data and deterministic test fixtures
- Automated tests and formatting checks
- A GitHub Actions pipeline that enforces formatting, linting, strict type checking, offline tests, build verification, secret scanning, and dependency/security checks
- A security and privacy section
- A contribution guide and intended MIT license
- Secret scanning and dependency checks in continuous integration

Before publication, the repository must pass a dedicated sensitive-data review covering Git history, tracked files, examples, screenshots, logs, and generated artifacts.

### 11.1 Continuous integration

The execution plan must include two GitHub Actions workflows:

1. **Required credential-free CI** — runs on every pull request and push to the default branch. It installs from the committed lockfile and runs formatting verification, linting, strict type checking, unit tests, deterministic provider-contract and integration tests, build verification, secret scanning, and dependency/security checks. Any required failure blocks merge.
2. **Protected Sandbox end-to-end tests** — runs only through manual dispatch in a protected GitHub environment after approval. It uses dedicated eBay Sandbox credentials and other non-production test credentials. It must never run for untrusted fork code, expose secrets in logs or artifacts, or contact Production endpoints.

Workflow permissions default to read-only. Third-party actions are pinned to full commit SHAs. Uploaded artifacts are allowlisted and must not contain private seller data, photos, provider payloads, tokens, databases, or logs with personal information. Once public, branch protection requires the credential-free workflow before merge.

## 12. Success criteria

The first release is successful when a seller can:

1. Supply photos, a description, defects, and target price.
2. Receive a source-backed listing proposal with explicit uncertainty.
3. Receive current shipping recommendations for Italy, EU continental Europe, and non-EU continental Europe.
4. Create an unpublished eBay draft that passes eBay validation.
5. Review one complete summary and approve the exact draft version.
6. Publish once without duplication and receive the live listing URL and ID.
7. Propose a later revision and be required to approve it before it affects the live listing.
8. Launch the app or change a listing and receive each newly observed offer, completed sale, or refund-status change once.

## 13. Deferred decisions for implementation planning

The execution plan will resolve these choices using current official documentation and small validation spikes where needed:

- Concrete frontend and local API frameworks
- OpenAI model and API surface for multimodal, source-backed research
- Initial shipping quote provider and fallback rate source
- eBay Inventory versus traditional listing API strategy for creation and continued Seller Hub compatibility
- Packaging and background-job libraries
- Operating-system secret storage implementation
- Exact CI commands, action versions, and protected-environment configuration after the implementation stack is selected

These decisions do not change the approved user workflow or safety boundaries.

## 14. Public technical references

- [eBay Inventory API overview](https://developer.ebay.com/api-docs/sell/inventory/static/overview.html)
- [eBay Account API overview](https://developer.ebay.com/api-docs/sell/account/static/overview.html)
- [eBay shipping rate tables](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/shipping-rate-tables.html)
- [eBay calculated shipping](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/shipping-calculated.html)
- [eBay Trading API `GetBestOffers`](https://developer.ebay.com/devzone/xml/docs/reference/ebay/GetBestOffers.html)
- [eBay Fulfillment API](https://developer.ebay.com/develop/api/sell/fulfillment_api)
