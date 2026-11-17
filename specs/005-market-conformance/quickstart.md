# Validate market conformance

From repository root, install uv 0.13.8 and make; uv resolves Python 3.14.10.

```powershell
uv --version
make install
make check-all
uv run pytest tests/unit/market --cov=rescue.market --cov-branch --cov-report=term-missing --cov-report=json --cov-fail-under=100
uv run pytest tests/architecture/market_layout tests/architecture/boundaries
uv run python -m rescue.demo
```

Require zero missed statements AND branches from coverage JSON, independently of rounded percentage. See [contracts](contracts/market.md) and [data model](data-model.md).

1. Execute 200+ seeded sequences over two missions and ships; after every step compare both ships to an independent ledger, reporting seed and trace on failure.
2. Hold then accept: HELD and ACCEPTED history with request ID; held becomes pending and usage stays unchanged.
3. Reject/expire: release only that hold. Refused/repeated operations preserve whole aggregate and history.
4. Lower availability below commitments: retain settled state, expose shortfall and refuse excess new holds. Missing availability also prevents holds.
5. Reject unknown statuses and conflicting same-time publications without publication.
6. Check every required docstring and adjacent rule document; check six categories, statuses and history in both UML and ER.

Integration tests must prove failed transactions publish neither history nor pending request and successful acceptance publishes both. Retain concurrency/outcome regressions through make check-all. Pure market tests use real values with no I/O or domain fakes.

## Demo bytes

Before further implementation, capture demo stdout bytes from the committed pre-feature baseline in an isolated temporary export or existing baseline workspace, using the pinned interpreter. Capture candidate stdout through a subprocess binary pipe and compare bytes and successful exit codes. Record baseline commit and command. PowerShell decoded output comparison is insufficient. Today's dirty demo is not a pre-feature baseline; if a trustworthy baseline is unavailable, report FR-009 unverified.
