# Quickstart: verify Clear and Ordered Communication

Prerequisites: uv 0.13.8, make and Mermaid CLI 11.17.0 (`mmdc`). See `AGENTS.md` section 1.

## 1. Capture the demo baseline (before any change)

```bash
uv run python -m rescue.demo > "$TMP/demo-before.txt"
```

Use any temporary path; the file exists only for the diff in step 5.

## 2. Gates

```bash
make install
make check-all
```

Expected:
- Lint passes.
- `check-architecture` passes, including `communication-isolated` and `communication-layers` ([import contracts](contracts/import-contracts.md)).
- The full suite passes.
- The `rescue/communication` coverage report shows 100% and does not fail `--fail-under=100`.

## 3. Pure rules

```bash
uv run pytest tests/unit/communication tests/architecture/communication_layout -q
```

Expected:
- Every row of the precedence table (research P6) and every recovery rejection (P8) has a passing case.
- One public name per file, the four-label docstrings and the diagram field checks all pass.

## 4. Stories end to end

```bash
uv run pytest tests/integration/application/communication tests/integration/application/concurrency tests/integration/experiments -q
```

Expected outcomes are in the [application contract](contracts/application-api.md) table:
- **Gaps**: the session shows `NotApplied` with the exact range.
- **Retries**: confirmed seats are counted once.
- **Replay**: reports keep their original ids and sequences, and the mission history is unchanged.
- **Races**: the first registered decision wins, and mission order numbers run 1..N with no gaps.
- **Copies**: a copied run continues its counters, and its source run is unchanged.

## 5. Behaviour unchanged for unsequenced calls

```bash
uv run python -m rescue.demo > "$TMP/demo-after.txt"
diff "$TMP/demo-before.txt" "$TMP/demo-after.txt" && echo identical
```

Expected: `identical`. The existing `tests/integration/application/communication/test_communication.py` passes unedited.

## 6. Boundary is enforced

Temporarily add `import rescue.mission` to `rescue/communication/rules/classify_delivery.py` and run `make check-architecture`. It must fail, naming `communication-isolated`. Revert the change.

## 7. Diagrams render

Re-render the four changed `.mmd` files with the commands in `docs/architecture/diagrams/rescue-domain-model/README.md` (Source and rendering) and open each `.svg`. Check that:
- the delivery shows `envelope`;
- the session owns its reports and gap notices;
- the decision report links to the history entry's `mission_sequence`;
- the ER title names Communication.
