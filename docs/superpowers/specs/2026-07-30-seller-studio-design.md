# Seller Studio Design

## Intent

Turn the functional eBay Listing Copilot into a polished seller workspace without changing its domain behavior or weakening the explicit approval boundary.

## Direction

The product should feel like a contemporary editorial commerce tool: warm paper-toned surfaces, precise sans-serif typography, crisp dark ink, and restrained use of eBay-inspired red, blue, yellow, and green as navigational signals. It must avoid a generic gradient-heavy “AI dashboard” aesthetic.

## Experience

- A sticky, compact shell communicates product identity, environment, and workflow position.
- Intake prioritizes photography with a purpose-built dropzone and visible file previews.
- Forms use stronger grouping, helpful microcopy, and clear primary/secondary hierarchy.
- Tables and read-only evidence remain information-dense but become responsive and scannable.
- Sandbox/production distinction remains prominent.
- Consequential approval remains visually heavier than every other action.

## Engineering Quality Bar

- No new runtime dependency is required.
- Semantic controls, visible focus, minimum 44px interactive targets, reduced-motion support, and responsive layouts are mandatory.
- Existing callbacks, payloads, routes, and tests remain compatible.
- New presentation behavior is covered through user-visible component tests.

