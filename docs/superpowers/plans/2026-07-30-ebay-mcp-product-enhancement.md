# eBay MCP Product Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the complete `ebay-mcp` tool catalogue to Listing Copilot through a private sidecar and a fail-closed execution gateway.

**Architecture:** A pinned Node sidecar exposes Streamable HTTP only to the FastAPI container over a private Docker network. FastAPI uses the official MCP Python SDK, classifies every tool from its annotations, executes reads directly, and requires a canonical hash-bound action approval for every mutation. Existing native adapters remain operational and preferred for current workflows.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, official MCP Python SDK 2.x, Node.js 22, `ebay-mcp` 1.14.2, React 18, TypeScript, Docker Compose

## Global Constraints

- Expose all `ebay-mcp` tool families, including duplicates.
- Never expose the MCP endpoint, bearer token, eBay credentials, or refresh token to the browser or public network.
- Treat absent or malformed `readOnlyHint` as mutating.
- Bind mutation approval to tool name, canonical arguments, environment, and annotations.
- Sandbox is the default; Production mutation and destructive execution are separate opt-ins.
- Never automatically retry an ambiguous mutation.
- Existing native adapters and workflows must continue working when MCP is disabled or unavailable.
- Pin `ebay-mcp` to `1.14.2`; do not use `latest`.
- Use `mcp>=2.0.0,<3.0.0`, the official Python SDK supporting Streamable HTTP.

---

### Task 1: Sidecar and configuration boundary

**Files:**
- Create: `Dockerfile.ebay-mcp`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`
- Test: `backend/tests/unit/test_config.py`

**Interfaces:**
- Produces settings `ebay_mcp_enabled: bool`, `ebay_mcp_url: str`,
  `ebay_mcp_auth_token: SecretStr`, `ebay_mcp_production_mutations: bool`,
  `ebay_mcp_production_destructive: bool`, and
  `ebay_mcp_max_result_bytes: int`.

- [ ] **Step 1: Write the failing configuration test**

```python
def test_mcp_defaults_fail_closed(monkeypatch):
    monkeypatch.delenv("EBAY_MCP_ENABLED", raising=False)
    settings = Settings(_env_file=None)
    assert settings.ebay_mcp_enabled is False
    assert settings.ebay_mcp_production_mutations is False
    assert settings.ebay_mcp_production_destructive is False
    assert settings.ebay_mcp_max_result_bytes == 1_000_000
```

- [ ] **Step 2: Run the test and confirm the fields are absent**

Run: `python -m pytest tests/unit/test_config.py -q`

- [ ] **Step 3: Add the MCP settings and official SDK**

Add `mcp>=2.0.0,<3.0.0` to backend dependencies and implement the exact
settings above. `ebay_mcp_url` defaults to
`http://ebay-mcp:3000/`; the bearer token defaults to an empty `SecretStr` and
must be non-empty when the integration is enabled.

- [ ] **Step 4: Create the pinned sidecar image**

```dockerfile
FROM node:22-bookworm-slim
RUN npm install --global ebay-mcp@1.14.2
USER node
CMD ["node", "/usr/local/lib/node_modules/ebay-mcp/build/serverHttp.js"]
```

Add an `ebay-mcp` Compose service with no `ports`, an internal
`ebay-mcp-internal` network, `MCP_PORT=3000`, `EBAY_MCP_TOOLS=all`,
`EBAY_READ_ONLY=false`, `EBAY_MCP_UI=off`, and environment-provided
credentials. Attach `app` to both `edge` and `ebay-mcp-internal`.

- [ ] **Step 5: Verify configuration and Compose rendering**

Run:

```bash
python -m pytest tests/unit/test_config.py -q
docker compose config
```

Confirm the sidecar has no published port and secrets are represented only by
variable names.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile.ebay-mcp docker-compose.yml .env.example backend/pyproject.toml backend/app/config.py backend/tests/unit/test_config.py
git commit -m "build: add private pinned ebay mcp sidecar"
```

### Task 2: MCP client and complete catalogue

**Files:**
- Create: `backend/app/integrations/ebay_mcp/client.py`
- Create: `backend/app/integrations/ebay_mcp/types.py`
- Create: `backend/app/integrations/ebay_mcp/__init__.py`
- Create: `backend/tests/contract/test_ebay_mcp_client.py`

**Interfaces:**
- Produces `McpToolDefinition`, `McpToolAnnotations`, `McpToolResult`, and
  `EbayMcpClient.list_tools()` / `EbayMcpClient.call_tool(name, arguments)`.

- [ ] **Step 1: Write contract tests against a fake MCP session**

Test that `list_tools()` preserves the full name, description, input schema and
annotations, including duplicate capabilities. Test that `call_tool()` passes
arguments unchanged, rejects protocol errors, and rejects results exceeding the
configured byte limit.

- [ ] **Step 2: Run tests and confirm the client is missing**

Run: `python -m pytest tests/contract/test_ebay_mcp_client.py -q`

- [ ] **Step 3: Implement typed MCP models**

```python
@dataclass(frozen=True)
class McpToolAnnotations:
    read_only: bool | None
    destructive: bool
    idempotent: bool

@dataclass(frozen=True)
class McpToolDefinition:
    name: str
    description: str
    input_schema: dict[str, object]
    annotations: McpToolAnnotations
```

Implement the client with `mcp.client.streamable_http.streamablehttp_client`
and `ClientSession`. Add `Authorization: Bearer <token>`, a 30-second timeout,
initialization, `list_tools`, and `call_tool`. Convert SDK objects at the
integration boundary so the application layer never imports SDK types.

- [ ] **Step 4: Prove complete-catalogue preservation**

Use a fixture containing read-only, mutating, destructive, and duplicate tools.
Assert no deduplication by description, family, or underlying endpoint.

- [ ] **Step 5: Run contract tests and commit**

```bash
python -m pytest tests/contract/test_ebay_mcp_client.py -q
git add backend/app/integrations/ebay_mcp backend/tests/contract/test_ebay_mcp_client.py
git commit -m "feat: add typed ebay mcp client"
```

### Task 3: Fail-closed tool policy and action envelope

**Files:**
- Create: `backend/app/domain/mcp_action.py`
- Create: `backend/app/application/mcp_policy.py`
- Modify: `backend/app/persistence/models.py`
- Create: `backend/migrations/versions/0005_mcp_actions.py`
- Create: `backend/tests/unit/application/test_mcp_policy.py`
- Create: `backend/tests/integration/test_mcp_action_persistence.py`

**Interfaces:**
- Produces `ToolRisk`, `McpActionEnvelope`, `McpToolPolicy.classify(tool)`,
  canonical `action_hash(envelope)`, and persisted `McpActionModel`.

- [ ] **Step 1: Write policy tests**

Cover these exact outcomes:

```python
assert classify(read_only=True, destructive=False) is ToolRisk.READ_ONLY
assert classify(read_only=False, destructive=False) is ToolRisk.MUTATING
assert classify(read_only=None, destructive=False) is ToolRisk.MUTATING
assert classify(read_only=True, destructive=True) is ToolRisk.DESTRUCTIVE
assert classify(read_only=False, destructive=True) is ToolRisk.DESTRUCTIVE
```

Also prove that changing the tool name, any nested argument, environment, or
annotation changes the SHA-256 action hash.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/unit/application/test_mcp_policy.py -q`

- [ ] **Step 3: Implement canonical action envelopes**

`McpActionEnvelope` contains:

```python
tool_name: str
arguments: dict[str, object]
environment: Environment
annotations: McpToolAnnotations
```

Canonicalize with sorted JSON keys and compact separators. Reject non-JSON
arguments, non-finite numbers, and payloads larger than 256 KiB before hashing.

- [ ] **Step 4: Add persistent action state**

Create `mcp_actions` with `id`, `tool_name`, `arguments_json`, `environment`,
`risk`, `payload_hash`, `status`, `approved_at`, `executed_at`,
`result_summary_json`, `provider_request_id`, and timestamps. Status values are
`PENDING_APPROVAL`, `APPROVED`, `EXECUTING`, `COMPLETED`, `FAILED`, and
`AMBIGUOUS`.

- [ ] **Step 5: Verify migration and persistence**

Run:

```bash
python -m pytest tests/unit/application/test_mcp_policy.py tests/integration/test_mcp_action_persistence.py -q
python -m alembic upgrade head
python -m alembic downgrade -1
python -m alembic upgrade head
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/domain/mcp_action.py backend/app/application/mcp_policy.py backend/app/persistence/models.py backend/migrations/versions/0005_mcp_actions.py backend/tests/unit/application/test_mcp_policy.py backend/tests/integration/test_mcp_action_persistence.py
git commit -m "feat: add hash-bound mcp action policy"
```

### Task 4: Safe MCP execution service

**Files:**
- Create: `backend/app/application/mcp_tools.py`
- Create: `backend/app/persistence/mcp_actions.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/unit/application/test_mcp_tools.py`

**Interfaces:**
- Produces `McpToolsService.catalogue()`, `run_read()`, `preview_mutation()`,
  `approve()`, and `execute_approved()`.

- [ ] **Step 1: Write service tests**

Prove:

- read-only tools execute without an action record;
- unannotated tools cannot use `run_read`;
- mutations cannot execute before approval;
- approval fails after any envelope change;
- Sandbox mutations can execute after approval;
- Production mutations and destructive actions obey their separate flags;
- a repeated completed idempotent action returns the stored result;
- a timeout or connection loss during mutation records `AMBIGUOUS` and does not
  retry;
- disabling MCP leaves native services unaffected.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/unit/application/test_mcp_tools.py -q`

- [ ] **Step 3: Implement the service**

Catalogue entries retain all upstream tools and add computed `risk` plus
`nativeCoverage: "primary" | "duplicate" | "mcp-only"`. The coverage map is
display metadata only and never removes a tool.

`run_read()` rechecks the current tool annotation immediately before calling.
`execute_approved()` reloads the stored envelope, recomputes its hash, atomically
changes `APPROVED` to `EXECUTING`, then calls MCP once. Network ambiguity becomes
`AMBIGUOUS`; it is never passed to generic retry logic.

- [ ] **Step 4: Wire lifecycle and kill switch**

When disabled or unconfigured, install `UnavailableMcpToolsService` whose
catalogue is empty and whose calls return a typed unavailable error. Do not
block application startup or native workflows when the sidecar is down.

- [ ] **Step 5: Run tests and commit**

```bash
python -m pytest tests/unit/application/test_mcp_tools.py -q
git add backend/app/application/mcp_tools.py backend/app/persistence/mcp_actions.py backend/app/main.py backend/tests/unit/application/test_mcp_tools.py
git commit -m "feat: gate ebay mcp execution"
```

### Task 5: Tool catalogue API

**Files:**
- Create: `backend/app/api/routes/mcp_tools.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/api/test_mcp_tools.py`

**Interfaces:**
- Produces:
  - `GET /api/ebay-tools`
  - `POST /api/ebay-tools/{tool_name}/run`
  - `POST /api/ebay-tools/{tool_name}/preview`
  - `POST /api/ebay-tool-actions/{action_id}/approve`
  - `POST /api/ebay-tool-actions/{action_id}/execute`

- [ ] **Step 1: Write API tests**

Assert catalogue search returns duplicates, read routes reject mutating tools,
preview never executes, approval returns the payload hash, execution rejects
hash mismatch, and destructive Production actions require both configuration
and an exact `confirm` string equal to the tool name.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/integration/api/test_mcp_tools.py -q`

- [ ] **Step 3: Implement Pydantic request and response models**

Requests accept only a JSON object named `arguments`. Preview responses include
tool, environment, risk, canonical arguments, hash, and warnings. Cap response
content at the configured result limit and replace upstream exception details
with a correlation ID.

- [ ] **Step 4: Register routes and verify**

Run: `python -m pytest tests/integration/api/test_mcp_tools.py -q`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/mcp_tools.py backend/app/main.py backend/tests/integration/api/test_mcp_tools.py
git commit -m "feat: expose guarded ebay tool api"
```

### Task 6: Searchable Tools workspace

**Files:**
- Create: `frontend/src/features/tools/ToolsWorkspace.tsx`
- Create: `frontend/src/features/tools/ToolInputForm.tsx`
- Create: `frontend/src/features/tools/ActionPreview.tsx`
- Create: `frontend/src/features/tools/ToolsWorkspace.test.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/app/router.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes the guarded API from Task 5.
- Produces a new `Tools` navigation tab without changing existing routes.

- [ ] **Step 1: Write component tests**

Test search, family/risk filters, duplicate entries, JSON-schema-derived inputs,
immediate read execution, mutation preview, exact hash display, approval, and
destructive confirmation. Assert raw bearer tokens and eBay credentials never
appear in props, DOM, or API types.

- [ ] **Step 2: Run tests and confirm failure**

Run: `npm test -- --run src/features/tools/ToolsWorkspace.test.tsx`

- [ ] **Step 3: Implement the catalogue**

Show name, family, description, `Read only` / `Approval required` /
`Destructive`, and native coverage. Preserve every entry from the backend; do
not merge duplicates.

- [ ] **Step 4: Implement schema inputs and result rendering**

Support string, number, integer, boolean, enum, array, and nested object JSON
Schema fields. For unsupported schema constructs, show a validated JSON object
editor rather than guessing. Render results as bounded formatted JSON in the
first release.

- [ ] **Step 5: Implement approval UX**

Read tools use `Run`. Mutations use `Review action`, then display the exact
tool, environment, arguments, warnings, and hash. Destructive actions require
typing the tool name before `Approve and execute` becomes enabled.

- [ ] **Step 6: Verify and commit**

```bash
npm test -- --run src/features/tools/ToolsWorkspace.test.tsx
npm run lint
npm run typecheck
git add frontend/src/features/tools frontend/src/api frontend/src/app/router.tsx frontend/src/styles/global.css
git commit -m "feat: add guarded ebay tools workspace"
```

### Task 7: Sold-comparable research enhancement

**Files:**
- Create: `backend/app/integrations/ebay_mcp/comparables.py`
- Modify: `backend/app/application/research.py`
- Modify: `backend/app/domain/research.py`
- Modify: `frontend/src/features/review/DraftReview.tsx`
- Create: `backend/tests/contract/test_ebay_mcp_comparables.py`
- Modify: `backend/tests/unit/application/test_research.py`
- Modify: `frontend/src/features/review/DraftReview.test.tsx`

**Interfaces:**
- Uses read-only tool `ebay_find_completed_items`.
- Adds provenance-labelled sold comparable records without changing draft
  approval fields.

- [ ] **Step 1: Write backend tests**

Given completed-item results, calculate median item price separately from
shipping, preserve currency, condition, sold date and listing URL, and reject
mixed-currency aggregation. If MCP is unavailable, research continues without
comparables and records a non-blocking warning.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
python -m pytest tests/contract/test_ebay_mcp_comparables.py tests/unit/application/test_research.py -q
```

- [ ] **Step 3: Implement the comparable source**

Call only `ebay_find_completed_items` through `run_read()`. Limit stored
comparables to 20 deterministic records ordered by sold date, retain source
URLs, and label every value as provider-sourced rather than AI-inferred.

- [ ] **Step 4: Add review presentation tests and UI**

Show comparable count, median, range, condition, sold date, shipping, and source
link. Never silently blend comparables into the target price or overwrite the
seller's chosen price.

- [ ] **Step 5: Verify and commit**

```bash
python -m pytest tests/contract/test_ebay_mcp_comparables.py tests/unit/application/test_research.py -q
npm test -- --run src/features/review/DraftReview.test.tsx
git add backend/app/integrations/ebay_mcp/comparables.py backend/app/application/research.py backend/app/domain/research.py backend/tests frontend/src/features/review
git commit -m "feat: add ebay sold comparables"
```

### Task 8: Security, deployment, and full verification

**Files:**
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `docs/deploy.md`
- Create: `docs/ebay-mcp.md`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Documents installation, threat boundary, package attribution, rollback, and
  Production enablement.

- [ ] **Step 1: Add CI checks**

Build the pinned sidecar image, run credential-free MCP gateway tests with a
fake server, scan both Python and npm dependency graphs, and verify Compose has
no host port for `ebay-mcp`.

- [ ] **Step 2: Document operations**

Document Sandbox setup, secret names, private-network topology, kill switch,
tool policy, ambiguous mutation recovery, package upgrade procedure, and MIT
attribution. State that enabling Production mutations is a separate manual
decision.

- [ ] **Step 3: Run the full repository verification**

```bash
cd frontend
npm ci
npm test -- --run
npm run lint
npm run typecheck
npm run build
cd ../backend
python -m pip install --editable ".[dev]"
python -m pytest -m "not sandbox"
ruff check .
mypy app
cd ..
python scripts/check_no_secrets.py
python scripts/verify_no_production_calls.py
docker compose config
docker build -f Dockerfile.ebay-mcp .
```

- [ ] **Step 4: Perform manual Sandbox acceptance**

Verify tool discovery, one read call, mutation preview without execution,
approval-hash invalidation, one explicitly approved reversible Sandbox
mutation, ambiguous-call handling, sidecar shutdown fallback, and absence of
credentials in logs.

- [ ] **Step 5: Commit and open a PR**

```bash
git add README.md SECURITY.md docs .github/workflows/ci.yml
git commit -m "docs: operationalize ebay mcp integration"
git push -u origin agent/ebay-mcp-integration
```

Open a pull request against `master`. Do not merge until protected CI and
manual Sandbox acceptance pass.
