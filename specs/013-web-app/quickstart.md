# Web App Validation Guide

These are intended checks after implementation; the exact browser test command and pinned dependency must be recorded when the runner is added.

1. Install the repository toolchain and run `make install`. Install the pinned browser-test dependency and its matching Chromium (`uv run playwright install chromium`).
2. Set `SPACE_RESCUE_ALLOWED_ORIGINS` to the exact frontend origin, for example `http://127.0.0.1:8001`. Start the API with `uv run uvicorn rescue.api.app:create_app --factory --host 127.0.0.1 --port 8000`. Serve `web/` separately with `python -m http.server 8001 --bind 127.0.0.1 --directory web`. Do not launch servers during planning.
3. Create a run and complete the ten-person demonstration: register mission and ships, mobilise, record a partial acceptance and refusal, mobilise again and confirm the remainder. Verify ten confirmed, zero pending, and complete visible outcomes.
4. Explore the same run, decisions and communication; exercise synchronisation and recovery without repeating seat effects. Run a configured comparison and verify its simulated baseline is labelled.
5. Exercise quote holds across two missions and verify capacity, final outcomes, error and lost-run feedback. Load history explicitly.
6. Run `make check-all` and the browser suite. Check keyboard-only use and 360/1440 px layouts. Verify each operation in [the UI contract](contracts/ui.md) and inspect complete results.

Runs and call histories are in memory and disappear on server restart. Repeated history reads can grow retained history substantially.
