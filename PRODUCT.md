# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

A single independent eBay seller (the app owner), operating their own inventory alone, with no team or multi-user roles. They use the app between other work — snapping photos of an item, then later approving a prepared draft — not in one continuous session.

## Product Purpose

eBay Listing Copilot turns a few item photos, a short description, known defects, and a target price into a complete, source-backed eBay draft (title, category, condition, item specifics, description, price, policies, shipping), which the seller reviews and explicitly approves before anything is published. It also tracks the seller's shipped and inbound packages, and surfaces new buyer offers/sales/refunds without polling.

## Positioning

Unlike generic listing tools that either fully automate publication or require the seller to manually assemble every field, this app front-loads research (product identification, comparable pricing, shipping costs) with visible provenance and uncertainty, but never publishes or revises a live listing without the seller approving the *exact* draft — enforced by a cryptographic hash binding, not a UI convention.

## Operating Context

- Runs locally on the seller's own machine (or a self-hosted server), never a shared/multi-tenant service.
- Sandbox and Production eBay environments are both used, with visibly distinct state — mixing them is a documented failure mode the UI must prevent.
- The seller reviews photos, researched facts (with source links and confidence), price, shipping-by-zone, policies, and warnings in one screen before an irreversible action (approve/publish).
- Notifications and tracking-status refreshes are checked at login/startup and after listing changes — never continuously — so the UI should not imply live/real-time updates.

## Capabilities and Constraints

Confirmed screens/flows: item intake (photos, description, defects, target price), draft review + approval, listing dashboard (local/eBay state, revisions), activity/notification center (offers, sales, refunds — read-only), package tracking (outbound linked-to-item and inbound personal packages, manual entry).

Constraints: no client-side router library (single-page, tab-style navigation is an accepted existing pattern, not necessarily binding for the redesign); desktop-first (a solo seller working at a desk with photos already on their computer), but must not break on a laptop-width viewport; no dark-pattern styling on the approval/publish action — it must read as deliberate and slightly weighty, not a routine "next" button.

Undecided: no confirmed brand name treatment, logo, or color beyond what a redesign proposes.

## Evidence on Hand

No real listings, product photography, or seller data exists — this is a pre-revenue personal tool. Any example content in the redesign must be clearly fictional (matching the project's existing "fictional examples only" rule for its public repo).

## Product Principles

- Evidence over polish-that-hides-uncertainty: inferred/unverified fields must stay visually distinguishable from confirmed ones, never blended in.
- The approval action is the one moment of real weight in the whole app; everything else can be calm and quiet.
- Read-only surfaces (activity, tracking) should look inert/informational, not actionable, since the app never auto-responds on the seller's behalf.
- Single-user tool, not a SaaS dashboard — avoid multi-tenant/enterprise dashboard tropes (org switchers, team avatars, seat counts) that don't apply here.

## Accessibility & Inclusion

No project-specific requirement beyond ordinary web accessibility (keyboard operability, sufficient contrast, form labels) — already a stated concern in the existing intake form implementation.
