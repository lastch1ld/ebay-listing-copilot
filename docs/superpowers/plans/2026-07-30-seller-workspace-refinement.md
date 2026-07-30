# Seller Workspace Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the intake and tracking screens into a calm seller workspace with a plain wordmark and one uniform numbered field hierarchy.

**Architecture:** Preserve the current React state and submission contracts. Introduce a shared presentational `numbered-field` structure in the existing feature components and style it through the existing global stylesheet; no new dependencies or backend changes.

**Tech Stack:** React 18, TypeScript, CSS, Testing Library, Vitest, Vite

## Global Constraints

- The intake headline is exactly `What are we selling?`.
- Every major field uses a plain sequential number, a label with supporting text, then its input.
- Remove the illustrated navbar mark and `Seller workspace` descriptor.
- Keep the Sandbox/Production indicator and all current routes and behavior.
- Avoid all-caps technical labels, `01/02` numbering, decorative gradients, strong shadows, and oversized controls.
- Replace README screenshots only after desktop and narrow-width visual review passes.

---

### Task 1: Plain brand lockup

**Files:**
- Modify: `frontend/src/app/App.test.tsx`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: `App({ environment }: { environment: Environment })`
- Produces: unchanged `App` API with a text-only `Listing Copilot` brand

- [ ] Write a failing test asserting `Listing Copilot` remains visible while `Seller workspace` and `.brand-mark` are absent.
- [ ] Run `npm test -- --run src/app/App.test.tsx` and confirm it fails for the old lockup.
- [ ] Remove the decorative mark and descriptor, delete obsolete CSS, and quiet the topbar without removing the environment badge.
- [ ] Run the focused test and confirm it passes.
- [ ] Commit as `style: simplify seller workspace header`.

### Task 2: Uniform numbered intake fields

**Files:**
- Modify: `frontend/src/features/intake/ItemIntakeForm.test.tsx`
- Modify: `frontend/src/features/intake/ItemIntakeForm.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: existing `IntakeSubmission` and `onSubmit`
- Produces: unchanged submission payload and four numbered visual field groups

- [ ] Write failing assertions for the exact headline and ordered field numbers `1` through `4`.
- [ ] Run `npm test -- --run src/features/intake/ItemIntakeForm.test.tsx` and confirm failure on the old `01/02` structure.
- [ ] Restructure photos, description, defects, and target price as `.numbered-field` blocks with number, label/supporting text, then control.
- [ ] Reduce hero size and whitespace; remove gradients and strong shadows; preserve responsive collapse below 760px.
- [ ] Run the focused tests and commit as `style: unify intake field hierarchy`.

### Task 3: Calm tracking form

**Files:**
- Create: `frontend/src/features/tracking/TrackingList.test.tsx`
- Modify: `frontend/src/features/tracking/TrackingList.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: existing `TrackingDirection`, `TrackingRecordDTO`, `onAdd`, and `onRefresh`
- Produces: unchanged tracking callbacks with five sequential numbered field groups

- [ ] Write a failing test for accessible labels and groups `1` through `5`.
- [ ] Run `npm test -- --run src/features/tracking/TrackingList.test.tsx` and confirm failure.
- [ ] Apply the shared hierarchy and concise supporting copy without changing state or callbacks.
- [ ] Run the focused test and commit as `style: refine tracking field hierarchy`.

### Task 4: Verification and screenshots

**Files:**
- Modify: `docs/images/app-intake.png`
- Modify: `docs/images/app-tracking.png`

- [ ] Run `npm test -- --run`, `npm run lint`, `npm run typecheck`, and `npm run build`.
- [ ] Capture and inspect intake/tracking at 1440×1050 and 390px widths.
- [ ] Confirm no clipping, inconsistent numbers, detached labels, excessive blank space, strong decorative effects, or horizontal overflow.
- [ ] Replace both README screenshots with reviewed desktop captures.
- [ ] Run `git diff --check`, inspect the final diff, and commit screenshots.
- [ ] Push the feature branch and open a pull request without merging.
