# Visual direction: Rescue operations dashboard

## Research used

Generated with UI/UX Pro Max CLI 2.15.0 on 2026-11-17. The broad operations dashboard product search matched analytics, financial and RPA dashboards; their product-specific palettes were not adopted. Targeted UX searches matched reduced-motion preference, mobile-first layout, form submission feedback, contextual live status and announced errors. A palette search returned dashboard palettes but no rescue-operations match, so the palette below is a design choice rather than a claimed database recommendation.

## Direction

Use a light, high-contrast mission operations console. Keep the information hierarchy calm and legible: a compact global header for run identity and connection/refresh state, two prominent tabs for Operations and Exploration, a mission summary row, and capability panels below. Exploration keeps the same run identity visible and labels experiment results as simulations.

Use a neutral slate canvas with white surfaces and restrained navy/blue accents. Reserve amber and red for warnings and errors, and pair every status colour with text and an icon or shape. Do not use red as the dominant brand colour or rely on green/red alone to encode acceptance.

Suggested tokens:

| Role | Value |
| --- | --- |
| Page background | `#F8FAFC` |
| Surface | `#FFFFFF` |
| Main text | `#0F172A` |
| Secondary text | `#475569` |
| Borders | `#CBD5E1` |
| Primary action | `#1D4ED8` |
| Focus ring | `#1D4ED8` |
| Success | `#166534` with text/icon |
| Warning | `#92400E` with text/icon |
| Error | `#B91C1C` with text/icon |

Use a readable sans-serif system stack, 16px body text, compact tabular numerals for quantities and identifiers, and a 1.5 body line height. Keep labels visible above inputs; use helper text for identifiers, units and timing. Show a concise result summary first, with the complete structured result in a keyboard-operable disclosure.

## Interaction and accessibility

- Design narrow screens first, then widen the mission summary and related records at larger breakpoints. At 360px, stack summary values and forms; avoid page-level horizontal scrolling.
- Maintain visible keyboard focus, logical tab order and a skip link. Keep focus visible when tab panels or feedback banners change.
- Give each input a persistent label. Show submission progress, then a success or error result. Associate field errors with controls and announce operation errors through an alert region.
- Announce meaningful live refresh changes without moving focus or creating competing live regions. Keep last-refresh time and stale state in text.
- Respect `prefers-reduced-motion`; use motion only to communicate state changes.
- Keep touch targets at least 44px where practical and provide spacing around adjacent actions.

## Source and limits

The UI/UX Pro Max searches were useful for dashboard structure and accessibility guidance, but no product-specific rescue result was found. These tokens and layout decisions are the implementation direction for this project and remain subject to visual review in the working browser app.
