# Repository Engineering and Credential Rules

These rules apply to every human contributor, coding agent, script, test, build, and release in this repository. They are mandatory unless a stricter platform policy applies.

## 1. Security priorities

1. Protect seller credentials, OAuth tokens, personal data, photos, and listing data.
2. Require explicit seller approval for consequential eBay actions.
3. Prevent duplicate, stale, or silently modified listings.
4. Keep the public repository reproducible without containing private operational data.
5. Prefer simple, reviewable implementations over clever or opaque ones.

## 2. Never collect account passwords

- Never request, accept, store, log, transmit, or autofill an eBay password, email password, or other account password.
- Authenticate with the provider's supported OAuth authorization flow.
- Never read browser cookies, saved passwords, browser profiles, or session storage to obtain authentication.
- Never ask a user to paste an OAuth authorization code, refresh token, API secret, or one-time verification code into chat, an issue, a commit, or an application log.

## 3. Secret classification

Treat all of the following as secrets or sensitive values:

- eBay application client secrets and OAuth access or refresh tokens
- OpenAI, shipping provider, search provider, and analytics keys
- OAuth authorization codes, PKCE verifiers, state values, and session secrets
- Seller IDs, private email addresses, addresses, phone numbers, and tax identifiers
- Production database contents, item photos, unpublished drafts, and operational logs
- Webhook signing secrets and encryption keys

Public application identifiers may be committed only when the provider explicitly documents them as non-secret and their inclusion has been reviewed.

## 4. Secret storage

- Store long-lived secrets in the operating-system keychain or an equivalent local secret store.
- Environment variables may be used for local bootstrap and CI injection, but real values must never appear in tracked files.
- `.env.example` may contain variable names, descriptions, and dummy values only.
- Never place secrets in frontend bundles, browser local storage, query strings, screenshots, fixtures, source maps, crash reports, or generated documentation.
- Persist refresh tokens only in the secret store. Keep access tokens in memory where practical and discard them when no longer needed.
- Do not implement homemade cryptography. Use maintained platform facilities and established libraries.
- Bind the local application to `127.0.0.1` by default. Do not expose it to a LAN or the internet without a separate authenticated deployment design.

## 5. OAuth requirements

- Use eBay's supported authorization-code flow and the narrowest scopes required for the implemented feature.
- Use and validate `state`; use PKCE whenever the provider and application type support it.
- Allow only preconfigured loopback callback addresses during local development.
- Validate callback errors, issuer expectations, and token responses before storing credentials.
- Separate Sandbox and Production client IDs, secrets, tokens, endpoints, databases, and visible UI state.
- Display the active environment prominently. Production actions must never fall back to Sandbox credentials or vice versa.
- Handle expiration and refresh-token rotation atomically. If rotation succeeds, replace the old token before continuing.
- Revocation, logout, or authorization failure must stop external actions without deleting local drafts.
- Never broaden OAuth scopes silently. A scope change requires documentation and renewed user consent.

## 6. Logging and error reporting

- Use structured logs with an allowlist of safe fields.
- Redact authorization headers, cookies, tokens, secrets, email addresses, postal addresses, and provider payload fields containing personal data.
- Do not log complete request or response bodies from authentication, seller-account, listing, or shipping endpoints.
- Give each external operation a generated correlation ID that contains no personal information.
- User-facing errors must explain the safe next step without exposing provider internals or credentials.
- Telemetry is off by default. Any future telemetry must be opt-in, documented, minimized, and scrubbed of listing and seller content.

## 7. Source-control rules

- Never commit `.env`, local databases, uploads, photos, tokens, logs, coverage artifacts containing source data, or provider response dumps.
- Maintain a defensive `.gitignore` before the first credentialed run.
- Run secret scanning on staged changes and in continuous integration.
- Enable GitHub secret scanning and push protection when the repository is published.
- Use fictional identities, products, addresses, and credentials in examples and tests.
- Do not paste secrets into commit messages, pull requests, issues, discussions, or CI output.
- Review the complete Git history—not only the current files—before making the repository public.

## 8. Credential incident response

If a secret may have been exposed:

1. Stop using it immediately.
2. Revoke or rotate it at the provider before attempting repository cleanup.
3. Remove it from the working tree and, when necessary, rewrite affected Git history.
4. Invalidate related sessions and refresh tokens.
5. Review logs and provider activity for misuse.
6. Document the incident without reproducing the secret.
7. Add or improve a test, scanner rule, or process control to prevent recurrence.

Deleting a secret from the latest commit is not sufficient once it has entered Git history.

## 9. Consequential-action rules

- Creating an unpublished draft may proceed within the user's requested workflow.
- Publishing, materially revising, relisting, or ending a listing requires explicit approval of a human-readable summary.
- Approval must be bound to the cryptographic hash of the normalized action payload.
- Any material change after approval invalidates that approval.
- Before executing, revalidate authentication, draft version, required fields, policy compatibility, and shipping-quote freshness.
- Use idempotency records and provider reconciliation to prevent duplicate listings.
- Do not automatically retry an ambiguous publish, revise, relist, or end operation until eBay state has been checked.
- Notifications are read-only. Never accept, counter, or decline an offer or issue a refund as a side effect of refreshing activity.
- Refresh activity once on application startup and once after a successful listing mutation. Do not introduce continuous polling without a separately approved design.
- Deduplicate activity using stable provider identifiers plus relevant status or revision values. Do not repeatedly alert on an unchanged event.
- Notification previews must minimize buyer information and must not expose addresses, email addresses, payment details, or provider payloads.

## 10. Coding standards

### 10.1 Architecture

- Keep the domain model independent of eBay, AI, search, and shipping-provider SDK types.
- Access every external service through a narrow adapter interface.
- Separate pure draft composition and validation from network transport.
- Keep modules focused on one responsibility and expose small, typed interfaces.
- Prefer dependency injection over hidden global clients.
- Do not introduce a distributed service, message broker, or cloud dependency when a local in-process component is sufficient.

### 10.2 Types and validation

- Use strict type checking.
- Validate all external input at system boundaries, including API responses, uploaded image metadata, URLs, money, dimensions, weights, country codes, and state transitions.
- Represent money as currency plus decimal value; never use binary floating-point arithmetic for monetary calculations.
- Store timestamps with timezone information and use UTC internally.
- Model provenance, confidence, and unknown values explicitly. Do not encode unknown as an empty string or fabricated default.
- Model Italy, EU continental destinations, and non-EU continental destinations as explicit shipping zones.

### 10.3 Functions and files

- Prefer small functions with descriptive names and explicit inputs and outputs.
- Avoid files that mix UI, domain logic, persistence, and provider calls.
- Remove dead code and unused dependencies instead of commenting them out.
- Explain why a non-obvious rule exists; do not narrate obvious syntax in comments.
- Avoid broad refactors unrelated to the active change.

### 10.4 External calls

- Set explicit timeouts for network calls.
- Retry only documented transient failures with bounded exponential backoff and jitter.
- Respect provider rate limits and `Retry-After` guidance.
- Cache taxonomy, policy, and research data only with documented freshness rules.
- Record source URLs and retrieval times for researched claims.
- Never treat a web-search snippet or inferred image detail as verified product data.
- Do not scrape sites that prohibit automated access or bypass authentication, CAPTCHAs, paywalls, or anti-bot controls.

### 10.5 Data and migrations

- Use versioned database migrations for every schema change.
- Make migrations reversible when practical and back up local data before destructive migration steps.
- Use transactions for approval, token rotation metadata, publish-operation records, and state transitions.
- Keep uploaded originals immutable; derived images must be stored separately with provenance.
- Provide deletion and export paths for local seller data.

### 10.6 User interface

- Show whether the app is connected to Sandbox or Production.
- Make uncertain, inferred, stale, and user-provided fields visually distinguishable.
- Keep known defects visible through intake, draft, approval, and publication.
- Summarize price differences, shipping assumptions, fees, customs issues, and destination exclusions before approval.
- Never use dark patterns, prechecked publication consent, or ambiguous buttons for consequential actions.
- After a successful action, show the listing ID, URL, exact action, and timestamp.

## 11. Testing rules

- Use test-driven development for new behavior and bug fixes: add a failing test, implement the smallest change, then refactor.
- Unit-test domain rules without network access.
- Use deterministic fixtures for provider contracts and research results.
- Use eBay Sandbox for automated end-to-end publication tests; never use a production listing as an automated test target.
- Test approval invalidation, duplicate prevention, stale shipping quotes, defect preservation, redaction, token expiration, and ambiguous publish recovery.
- Test notification deduplication, startup refresh, post-mutation refresh, partial API failure, and buyer-data minimization.
- Add regression tests for every fixed defect.
- Keep tests independent, deterministic, and safe to rerun.
- Do not weaken or delete a failing test merely to make CI pass without explaining and correcting the underlying requirement.

## 12. Dependency and supply-chain rules

- Prefer maintained libraries with narrow scope, compatible licenses, and healthy release practices.
- Pin direct dependencies and commit the lockfile.
- Review new dependencies for necessity, permissions, install scripts, known vulnerabilities, and transitive weight.
- Enable automated vulnerability and dependency-update checks.
- Do not execute downloaded scripts or generated code without inspection and version pinning.
- Verify official package names to avoid dependency-confusion and typosquatting attacks.

## 13. Change workflow

For every behavior change:

1. Restate the requirement and affected safety boundary.
2. Add or update tests first.
3. Implement the smallest coherent change.
4. Run formatting, linting, type checking, unit tests, and relevant integration tests.
5. Review logs and fixtures for sensitive information.
6. Update documentation when behavior, configuration, scopes, or external contracts change.
7. Inspect the final diff and commit only intentional files.

Security-sensitive changes involving OAuth, secret storage, publishing, approval, redaction, or GitHub release require an additional focused review.

## 14. Continuous-integration pipeline

- Use GitHub Actions as the public repository's continuous-integration platform.
- Run the safe, credential-free pipeline on every pull request and push to the default branch.
- The required pipeline sequence is: dependency installation from the lockfile, formatting verification, linting, strict type checking, unit tests, deterministic integration tests, build verification, secret scanning, and dependency/security scanning.
- Fail the workflow on any failed required check. Do not use `continue-on-error` for required quality or security gates.
- Upload only artifacts known not to contain credentials, personal data, item photos, listings, provider payloads, or local databases.
- Use least-privilege workflow permissions. Default the repository token to read-only and grant narrow write permissions only to jobs that demonstrably need them.
- Pin third-party actions to full commit SHAs and document update procedures.
- Do not expose repository secrets to workflows triggered from forks or untrusted pull requests.
- Keep eBay Sandbox and other credentialed end-to-end tests in a separate, manually dispatched, protected workflow environment.
- Credentialed jobs must use dedicated Sandbox credentials, require approval, redact output, and never target Production endpoints.
- Add concurrency controls so a newer run can cancel an obsolete run for the same branch when safe.
- Cache dependencies only by lockfile hash and never cache secret stores, `.env` files, databases, uploads, or provider responses.
- Branch protection should require the credential-free pipeline before merge once the repository is public.

## 15. Public-release checklist

Before the repository becomes public:

- Confirm the working tree and full Git history contain no real secrets or personal data.
- Run at least two independent secret scanners plus manual searches for provider key patterns, emails, addresses, and tokens.
- Verify `.gitignore`, `.env.example`, sample data, screenshots, test fixtures, CI logs, and generated artifacts.
- Confirm all examples use fictional data.
- Confirm production endpoints cannot be reached by default tests.
- Confirm the README documents required accounts, external costs, permissions, limitations, and the approval model.
- Add `SECURITY.md`, a license, contribution guidance, and a private vulnerability-reporting path.
- Run the complete test and security-check suite from a clean checkout.
- Confirm the required GitHub Actions workflow passes and the protected Sandbox workflow cannot expose credentials to untrusted code.
- Require the repository owner to approve the exact content before publication.
