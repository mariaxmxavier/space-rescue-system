# Quickstart: verify Mission Conformance

Prerequisites: uv 0.13.8, make, Mermaid CLI 11.17.0 (`mmdc`). See `AGENTS.md` §1.

## 1. Capture the demo baseline (before any change)

```bash
uv run python -m rescue.demo > /tmp/demo-before.txt
```

Use the scratchpad or any temp path; the file is only for the diff in step 4.

## 2. Gates

```bash
make install
make check-all
```

Expected: lint, `check-architecture` (including `mission-isolated` and `mission-layers`), and the
full suite pass; the `rescue/mission` coverage report shows 100% and does not fail
`--fail-under=100`.

## 3. Mission-only checks

```bash
uv run pytest tests/unit/mission tests/architecture/mission_layout -q
```

Expected: the invariant table (5 outcomes × every reachable state), one-public-name-per-file,
four-part docstrings, and code ↔ 8-diagram field agreement all pass.

## 4. Behaviour unchanged

```bash
uv run python -m rescue.demo > /tmp/demo-after.txt
diff /tmp/demo-before.txt /tmp/demo-after.txt && echo identical
```

Expected: `identical`.

## 5. No mission literals outside mission

```bash
grep -rnE "\.(outcome|status|action)\s*(==|!=|in|not in)\s*[\"{(]" rescue --include=*.py | grep -v "^rescue/mission"
```

Expected: no line compares a mission outcome, progress status or history action to a string.
Market RFQ and quote statuses may still appear (they belong to spec 005).

## 6. Boundary is enforced

Temporarily add `import rescue.market` to `rescue/mission/models/vocabulary.py`, run
`make check-architecture`, see it fail naming `mission-isolated`, then revert.

## 7. Diagrams render

Re-render each changed `.mmd` with the commands in
`docs/architecture/diagrams/rescue-domain-model/README.md` (Source and rendering) and open the
`.svg` in a browser: `SeatRequest` shows its five id fields, `Mission` owns `RequestHistoryEntry`,
and `RequestTiming` and the three enumerations appear.
