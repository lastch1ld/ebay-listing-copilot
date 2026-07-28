# Approval, notification, and privacy model

## Approval is bound to an exact draft

Every draft is canonicalized to a stable JSON payload (sorted keys, decimals
as strings, UTF-8) and hashed with SHA-256
(`app/application/approval.py:canonicalize`, `payload_hash`). Approving a
draft records that exact hash. Any later change — including reopening a
proposed revision — produces a different hash, so:

- `ApprovalService.matches(approval, draft)` returns `False` for a changed
  draft, and
- publishing or applying a revision re-checks the approval's hash against the
  current draft before doing anything (`application/publishing.py`,
  `application/listing_management.py`).

There is no way to publish or revise a listing with a payload that differs
from what was actually approved.

## Publication and revisions are idempotent

Publish, revision, and withdrawal each use an idempotency key stored in
`OperationRepository` (`publish:{offer_id}:{hash}`,
`revise:{offer_id}:{hash}`, `withdraw:{offer_id}:{hash}`). A repeated request
with the same key returns the already-recorded result instead of calling eBay
again — so retries, double-clicks, or network resends cannot create a
duplicate listing or apply the same revision twice.

## Notifications and tracking refresh are read-only and trigger-based

- **Activity** (`application/activity.py`): refreshed once at startup and
  once after a successful publish/revise/withdraw. Never polls on a timer.
  Never calls an offer-accept, counter, decline, or refund-issuing endpoint —
  the eBay adapters behind it (`integrations/ebay/trading.py`,
  `fulfillment.py`) expose no write methods at all.
- **Tracking** (`application/tracking.py`): refreshed once at login/startup
  for every non-delivered record, or on demand for a single record. Never
  writes to eBay or to the carrier — it only reads a carrier status.

Both deduplicate by a stable identifier plus the value that represents a
material change, so an unchanged event is never re-alerted, and a source's
temporary failure only marks that source as failed without discarding
results already fetched from other sources in the same refresh.

## What is stored, and where

- **Local SQLite** (`backend/data/app.db`, gitignored): items, photos'
  metadata (not raw bytes), research claims with provenance, draft versions
  and their hashes, approvals, publish/revision/withdrawal operation records,
  shipping quotes, activity events, and tracking records.
- **Uploaded photo originals** (`backend/data/uploads/`, gitignored): stored
  content-addressed by SHA-256, never overwritten.
- **OS keychain** (via `keyring`): eBay OAuth refresh tokens only, scoped per
  environment (`ebay.sandbox.refresh_token` / `ebay.production.refresh_token`
  — see `EbayTokenStore`) so a Sandbox token is never usable against
  Production or vice versa.
- **Nowhere:** account passwords (never requested or stored), buyer
  addresses/emails/payment details (redacted from logs and excluded from
  notification content by design — see `app/security/redaction.py`), and
  full provider response payloads (only extracted, normalized fields are
  kept).

## Deletion and export

Because everything lives in a single local SQLite file plus the uploads
directory, full deletion is: stop the app, delete `backend/data/`, and
(optionally) clear the `ebay-listing-copilot` keychain entries via your OS's
credential manager or `keyring` CLI. There is currently no in-app per-item
delete/export button — see the repository issues for that as a possible
follow-up.

## Incident response

If a credential is ever exposed (committed by mistake, logged, etc.), follow
[`AGENTS.md`](../AGENTS.md#8-credential-incident-response): revoke it at the
provider first, then clean up the working tree/history, invalidate sessions,
and add a test or scanner rule so the same mistake is caught automatically
next time.
