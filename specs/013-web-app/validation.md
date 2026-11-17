# Web app and simulation viewer validation

Validated on 2026-11-17 with uv 0.13.8, Python 3.14.10 and pinned Playwright Chromium.

- `make install` installed locked dependencies.
- `make check-all` passed: Ruff, all 18 import contracts, 1,571 tests and every configured branch-coverage gate. Two warnings were reported.
- `uv run python -m rescue.demo` completed with 10 confirmed seats and zero pending.
- Real API tests execute baseline, all10, all11 and all12, check evidence and final state, and verify independent concurrent preparations. The all12 test checks shortfall, finality, delayed and out-of-order responses, competing requests, invalid quantities and replay.
- Browser journeys cover playback, seeking, responsive layout, reduced motion, failure recovery, rescue coordination, shared-capacity quotes, communication recovery, inspection and two-policy comparison. A browser inventory checks all 22 public operations.
- Independent review identified fixes for run-creation races, stale inspection data, call-history status labels and tab capability restoration.

Runs and histories are held in memory. See [quickstart](quickstart.md) for startup and usage.
