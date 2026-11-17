# Validation

- `uv run pytest tests/integration/api/http -q --no-cov`: 4 passed.
- `make check-all`: passed, including formatting, Ruff, 16 import contracts, 1,499 tests and package coverage gates.
- `uv run python -m rescue.demo`: passed; 10 confirmed seats, 0 pending, complete.
- Quickstart commands use the documented loopback Uvicorn entrypoint and generated `/docs` page.

The HTTP test client emits a Starlette deprecation warning for HTTPX; tests pass. The dependency pins remain exact.
