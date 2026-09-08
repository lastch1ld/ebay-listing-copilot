# Seller Workspace Refinement

## Goal

Make the eBay Listing Copilot feel like a calm, approachable workspace for a
seller rather than a technical administration dashboard. Preserve all existing
workflow behavior.

## Header and navigation

- Replace the illustrated multicolour brand mark and technical subtitle with a
  plain `Listing Copilot` wordmark.
- Keep the environment indicator because Sandbox versus Production is a safety
  requirement, but render it quietly.
- Preserve the existing navigation labels and routes.

## Intake content

- Use the exact page headline `What are we selling?`.
- Replace the mixed section-heading treatment with one repeated vertical
  pattern for every major form field:
  1. A plain sequential number (`1`, `2`, `3`, `4`)
  2. A label and short supporting sentence on the same line
  3. The associated input
- Apply the pattern to photos, description, defects, and target price.
- Keep `No known defects` directly associated with the defects field.
- Keep validation, submission data, photo previews, and approval messaging
  unchanged.

## Visual direction

- Reduce oversized display typography and excess vertical whitespace.
- Use a warm, restrained surface with softer borders and moderate radii.
- Avoid decorative iconography, all-caps technical labels, numbered `01/02`
  markers, strong shadows, gradients, and dashboard-like status decoration.
- Keep controls comfortably sized without making them dominate the page.
- Preserve responsive single-column behavior on narrow screens.

## Tracking screen

- Bring the tracking form into the same numbered field rhythm where applicable.
- Reduce the unfinished appearance created by oversized empty controls and
  unused space.
- Preserve the tracking data contract and empty-state behavior.

## Verification

- Component tests assert the exact intake headline and the accessible field
  structure.
- Existing frontend tests, lint, type checking, and production build pass.
- Fresh intake and tracking screenshots are reviewed at desktop and narrow
  widths for clipping, inconsistent numbering, awkward whitespace, and
  navigation regressions.
- README screenshots are replaced only after the application itself passes the
  visual review.
