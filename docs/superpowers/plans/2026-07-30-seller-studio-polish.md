# Seller Studio Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the eBay Listing Copilot presentation as a responsive, accessible seller studio while preserving all business behavior.

**Architecture:** Keep the existing React feature boundaries and callbacks. Add presentation semantics to the app shell and intake component, then implement the visual system centrally in `global.css` so every existing feature benefits without a broad component rewrite.

**Tech Stack:** React 18, TypeScript, CSS custom properties, Testing Library, Vitest, Playwright

## Global Constraints

- Preserve all existing routes, callback signatures, approval safeguards, and environment behavior.
- Add no runtime dependency.
- Maintain visible Sandbox and Production state.
- Support reduced motion and narrow viewports.

---

### Task 1: Seller studio shell

**Files:**
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/app/App.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: `Environment` and `AppRouter`
- Produces: semantic `.app-shell`, `.app-topbar`, `.brand-mark`, and `.environment-status` presentation hooks

- [ ] **Step 1: Write the failing test**

Add assertions that the header exposes “Seller workspace” supporting copy and an accessible environment status.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run src/app/App.test.tsx`
Expected: FAIL because the supporting copy and status semantics are absent.

- [ ] **Step 3: Implement the shell**

Add the semantic shell copy and status hook without changing routing.

- [ ] **Step 4: Implement the visual tokens and shell**

Replace the current neutral primitives with the approved editorial-commerce tokens, sticky shell, responsive navigation, focus states, and reduced-motion behavior.

- [ ] **Step 5: Verify**

Run: `npm test -- --run src/app/App.test.tsx`
Expected: PASS.

### Task 2: Photo-first intake

**Files:**
- Modify: `frontend/src/features/intake/ItemIntakeForm.tsx`
- Modify: `frontend/src/features/intake/ItemIntakeForm.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: existing `IntakeSubmission`
- Produces: `.photo-dropzone`, `.photo-preview-grid`, and file-count announcement while preserving the submitted `File[]`

- [ ] **Step 1: Write the failing test**

Assert that the photo control exposes supported formats, announces selected files, and renders one preview label per selected image.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run src/features/intake/ItemIntakeForm.test.tsx`
Expected: FAIL because photo guidance and preview labels are absent.

- [ ] **Step 3: Implement photo-first markup**

Add a label-driven dropzone, guidance, selected-file preview tiles, and structured form header. Keep validation and submission unchanged.

- [ ] **Step 4: Style the intake workspace**

Add responsive asymmetrical layout, polished fields, checkbox, alerts, and action row.

- [ ] **Step 5: Verify**

Run: `npm test -- --run src/features/intake/ItemIntakeForm.test.tsx`
Expected: PASS.

### Task 3: Cross-feature polish and release evidence

**Files:**
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: existing `.card`, `.table`, `.badge`, `.button`, `.empty-state`, `.two-column`
- Produces: responsive, accessible styling shared by review, listings, activity, and tracking

- [ ] **Step 1: Add responsive shared treatments**

Implement overflow-safe tables, elevated empty states, refined badges, loading/status surfaces, and mobile stacking.

- [ ] **Step 2: Run complete verification**

Run: `npm run lint && npm run typecheck && npm test -- --run && npm run build`
Expected: all commands pass.

- [ ] **Step 3: Inspect the production build**

Serve the build and capture desktop and mobile screenshots of intake and tracking for visual review.

- [ ] **Step 4: Review the diff**

Confirm no secrets, provider behavior, routes, payloads, or consequential-action safeguards changed.

