# Research: Rescue Web App

## Browser architecture

**Decision**: HTML, CSS and JavaScript modules grouped by capability, with a common run workspace and transport boundary. **Rationale**: The roadmap selects these technologies and the repository has no frontend toolchain. **Alternatives**: A framework adds unneeded infrastructure; a generic command console obscures workflows and guided input.

## API and local access

**Decision**: Serve static assets locally and explicitly configure the API's allowed frontend origin. **Rationale**: `rescue/api/app.py` checks POST origins against the allowlist even for same-origin calls; there is no run-list endpoint. Decimal values are strings or integers, not JSON floats. Business rejection may arrive with HTTP 200, so inspect status, reason and value. **Alternative**: weakening origin policy changes existing behaviour unnecessarily.

## State and history

**Decision**: Refresh state explicitly and after mutations, tracking run identity and request generation; retain and mark the last successful snapshot stale on failure. Load call history only on explicit request. **Rationale**: Every state read enters history and each history read retains its complete prior response, causing rapidly growing memory use. Do not automatically retry uncertain mutations. **Alternative**: polling history and optimistic seat accounting risk resource growth and incorrect presentation.

## Comparison

**Decision**: Both tabs share the main run; comparison outputs are labelled simulations with their configured scenario baseline. **Rationale**: `compare` uses configured scenario baselines and policies, not the changing live mission state. Policies and scenarios are supplied on run creation. **Alternative**: portraying a baseline as the live run would be misleading.

## Browser verification

**Decision**: Add a pinned Playwright Python browser suite alongside existing checks. **Rationale**: Python-only tests cannot establish browser keyboard, interaction and responsive behaviour; [Playwright recommends its pytest plugin](https://playwright.dev/python/docs/intro). Pin a verified exact version when installing, and its corresponding browser revision. **Alternative**: manual-only checks do not give repeatable evidence.

## UI/UX Pro Max

**Decision**: CLI 2.15.0 was installed and initialised for Codex. Two design-system queries returned marketing landing-page patterns unsuitable for an operations dashboard, so no generated system is adopted; apply the skill's general accessibility guidance as fallback and refine visual choices during implementation. **Rationale**: [The package instructions](https://www.npmjs.com/package/ui-ux-pro-max-cli) document `uipro init --ai codex`; the skill requires checking query fit. **Alternative**: presenting an unsuitable match as verified would mislead the implementer.
