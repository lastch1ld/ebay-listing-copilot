# eBay MCP Product Enhancement

## Goal

Add the full `ebay-mcp` catalogue to Listing Copilot while preserving the
pilot's purpose-built workflows and preventing any MCP tool from bypassing
human approval, environment separation, idempotency, or reconciliation.

## Runtime architecture

`ebay-mcp` runs as a pinned Node sidecar on a private Docker network. It has no
published host port. The FastAPI backend is its only client and authenticates
with a dedicated bearer token. The React frontend never receives MCP
credentials or calls the sidecar directly.

The sidecar advertises all tool families, including functionality duplicated by
native adapters. Native adapters remain the preferred implementation for
existing listing publication and activity flows. The MCP catalogue supplies
additional tools, fallback coverage, and sold-listing research.

## Tool policy

Tool definitions are classified from MCP annotations:

- `readOnlyHint: true`: may execute without approval.
- `readOnlyHint: false` or absent: requires an approved action envelope.
- `destructiveHint: true`: additionally requires destructive-action
  confirmation and is disabled in Production unless explicitly enabled.
- Missing or malformed annotations fail closed as mutating.

The backend stores an immutable action envelope containing the tool name,
canonical arguments, environment, annotations, and SHA-256 payload hash.
Approval is bound to that exact envelope. Any argument, tool, or environment
change invalidates approval. Mutations receive an idempotency key and ambiguous
results are never retried automatically.

## Product surfaces

A new **Tools** tab provides a searchable catalogue, including duplicate tools.
It shows the tool family, description, risk class, input schema, and whether the
native pilot already covers the capability.

Read-only tools can run immediately and display structured JSON results.
Mutating tools first create a preview with the exact arguments and environment.
The seller must approve that preview before execution. Destructive actions use
explicit language naming the operation and target.

The existing research stage calls `ebay_find_completed_items` to add sold
comparables, price ranges, listing URLs, conditions, and sale dates with visible
provenance.

## Failure and security behavior

- Sandbox remains the default.
- Production mutations are disabled by default.
- If the sidecar is unavailable, existing native workflows continue to work.
- Tool-list and read failures are surfaced without credentials or raw provider
  payloads.
- Sidecar results are size-limited before persistence or frontend delivery.
- Credentials remain outside Git and logs.
- The integration has a single kill switch.
- The package and container are pinned and included in dependency scanning.

## Compatibility

The existing frontend routes, native eBay adapters, OAuth flow, database
records, approval flow, and publishing service continue to work. MCP introduces
additive routes and storage; it does not replace existing behavior.
