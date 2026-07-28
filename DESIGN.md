---
name: eBay Listing Copilot
description: Calm, evidence-forward Operate-mode admin tool for a solo eBay seller
colors:
  bg: "#faf8f5"
  surface: "#ffffff"
  surface-alt: "#f1eee9"
  border: "#e3ddd3"
  border-strong: "#cfc6b8"
  text: "#211d17"
  text-secondary: "#6b655b"
  text-muted: "#948c7e"
  accent: "#9c6b1f"
  accent-hover: "#7f5717"
  accent-contrast: "#fffaf0"
  accent-tint: "#f4e9d8"
  danger: "#a3341c"
  danger-tint: "#f8e8e3"
  success: "#2e6b3e"
  info-tint: "#eef1f7"
typography:
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    lineHeight: 1.5
  h1:
    fontSize: "1.875rem"
    fontWeight: 600
  h2:
    fontSize: "1.25rem"
    fontWeight: 600
  h3:
    fontSize: "1.125rem"
    fontWeight: 600
  small:
    fontSize: "0.875rem"
  caption:
    fontSize: "0.8125rem"
rounded:
  sm: "6px"
  md: "10px"
spacing:
  1: "0.25rem"
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  5: "1.5rem"
  6: "2rem"
  7: "3rem"
  8: "4rem"
components:
  button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "{spacing.2} {spacing.4}"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-contrast}"
    rounded: "{rounded.sm}"
    padding: "{spacing.3} {spacing.5}"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.5}"
  badge:
    backgroundColor: "{colors.surface-alt}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
  badge-accent:
    backgroundColor: "{colors.accent-tint}"
    textColor: "{colors.accent-hover}"
---

## Overview

An Operate-mode admin tool for one solo eBay seller — not a marketing surface. The
system is deliberately quiet: restrained neutral palette, a single system-sans
stack, and exactly one reserved accent color (a deep amber, evoking a wax seal /
provenance stamp) spent only on the primary "Approve this exact draft" action,
the active nav tab, and focus rings. Everything else — listings, activity,
tracking — stays informational and low-key, since those surfaces are read-only
or low-stakes by design. See `PRODUCT.md` for the product record this system
serves.

## Colors

Restrained strategy (the Operate default): warm off-white background
(`--color-bg`), white card surfaces (`--color-surface`), and a second, slightly
warmer neutral layer (`--color-surface-alt`) for the top bar and nav. The
amber accent (`--color-accent`) is reserved — it must never appear as a
decorative flourish, only on the approve button, the active tab underline, and
badges explicitly marking evidence/provenance. Semantic colors (`--color-danger`,
`--color-success`) are used only for their named state, never as a generic
brand color substitute.

## Typography

One family throughout (system-ui sans stack) at a 1.125 scale ratio, fixed rem
sizes (no fluid/clamp type — this is a desktop admin tool viewed at a
consistent DPI). Headings are 600 weight; body copy is regular weight at
1.5 line-height. No display/body font pairing — Operate surfaces don't need
one, and a second face here would read as noise, not craft.

## Layout

A slim top bar (product name + environment badge) sits above a tab-style nav
(`.app-nav`), both on the alt-neutral surface. Content is a single centered
column, max-width 960px, padding via `--space-6` (`--space-4` on narrow
viewports). The intake form is the one two-column layout (`.two-column`,
photo input left, text fields right on desktop), collapsing to one column
below 720px — every other screen is a single column of cards, since Operate
density favors clarity over horizontal packing at this scale.

## Elevation & Depth

Flat by design: 1px borders (`--color-border` / `--color-border-strong`)
separate cards and table rows, never shadows. This is a deliberate tonal-layering
system, not an oversight — shadows read as decoration on an admin tool this
quiet.

## Shapes

Two radii only: `--radius-sm` (6px) for controls, inputs, badges, and buttons;
`--radius-md` (10px) for cards. No pill shapes, no sharp corners — consistent
soft-cornered rectangles throughout.

## Components

- **`.card`**: the base content container — white surface, 1px border,
  `--radius-md`, `--space-5` padding. Stacked cards get `--space-5` between
  them (`.card + .card`).
- **`.button`** / **`.button--primary`**: the primary variant is reserved for
  the one weighty action per screen (approve, submit intake, add tracking
  number) — a screen should have at most one `.button--primary`; everything
  else (propose revision, refresh now, mark read) is a plain `.button`.
- **`.field`**: label-above-input group, `--space-4` bottom margin;
  `.field--checkbox` lays the checkbox and its label out horizontally instead.
- **`.badge`** / **`.badge--accent`**: inline status/provenance tags. Accent
  badges are reserved for evidence provenance (Inferred/Source verified/etc.)
  and activity event types — never for arbitrary emphasis.
- **`.table`**: dense, border-bottom rows, no zebra striping, no shadows.
- **`.empty-state`**: dashed border, centered muted text — used for every
  "nothing here yet" case instead of inventing a new empty-state per screen.
- **`.alert`** / **`.status`**: `.alert` is red-tinted for form errors and
  blocking warnings (customs, missing shipping rate); `.status` is
  neutral-tinted for a plain confirmation (e.g. "Item created: …").

## Do's and Don'ts

- Do reserve the accent color for exactly the three uses named above; don't
  spread it across nav icons, dividers, or card borders.
- Do keep every screen to at most one `.button--primary`; don't make two
  actions compete for primary weight on the same screen.
- Do use `.empty-state` for every empty list; don't write a bespoke "No X yet"
  paragraph per feature.
- Don't add shadows, gradients, or glass effects — the flat/bordered system is
  the committed look, not a placeholder for a later polish pass.
- Don't introduce a second typeface for "emphasis" — use weight and size from
  the existing scale instead.
