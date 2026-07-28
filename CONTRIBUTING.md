# Contributing

This is primarily a personal reference project, but contributions that keep
its safety guarantees intact are welcome.

## Before you start

Read [`AGENTS.md`](AGENTS.md) first — it is the mandatory rulebook for this
repository (credential handling, testing, coding standards, CI, and the
public-release checklist). Every change must follow it.

## Workflow

1. Open an issue describing the change before starting non-trivial work.
2. Follow test-driven development: add a failing test, make the smallest
   change that passes it, then refactor.
3. Use only fictional identities, products, addresses, and credentials in
   tests, fixtures, and examples — never real seller or buyer data.
4. Run the full local check suite before opening a pull request:

   ```bash
   cd backend && python -m ruff check . && python -m mypy app && python -m pytest -m "not sandbox" -q
   cd ../frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build
   python scripts/check_no_secrets.py
   ```
5. Keep pull requests scoped to one change. Update documentation when
   behavior, configuration, scopes, or external contracts change.

## Security-sensitive changes

Changes touching OAuth, secret storage, publishing, approval, or redaction
require extra care — see [`AGENTS.md`](AGENTS.md#13-change-workflow) for the
required review step. Report vulnerabilities privately per
[`SECURITY.md`](SECURITY.md) rather than in a public issue or pull request.

## Sandbox and Production

Never point a pull request's tests or CI changes at real eBay Production
endpoints. The `sandbox-e2e` workflow is manually dispatched and protected;
it is not runnable by external contributors without maintainer approval.
