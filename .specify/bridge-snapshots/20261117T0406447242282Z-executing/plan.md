# Implementation Plan: Market Conformance

**Branch**: `005-market-conformance` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Conform the market in place: six category packages, immutable entities, named statuses, append-only history and a market-owned structural inventory interface. Existing uncommitted implementation is a candidate to verify, not evidence of completion. Preserve pre-existing behaviour and demo bytes except for the new history.

## Technical Context

- Python 3.14.10; uv 0.13.8; standard-library runtime, no new dependencies.
- Exact dev pins: Ruff 0.17.5, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3, import-linter 2.16.
- Storage: immutable B3Market inside RunState; existing transaction store publishes successful replacements. Durable persistence belongs to 003.
- Platform: local Python application and CLI demo, including Windows.
- Testing: pure rules, seeded sequences, architecture, integration and demo regressions.
- Scope: one capability, six categories; 200+ sequences over at least two missions and ships.
- Constraints: market imports only itself, rescue.values and standard library; 100% line and branch coverage. No new performance target; retain in-memory operation.

## Constitution Check

| Gate | Before research | After design |
|---|---|---|
| Safe accounting | PASS: retain shared capacity | PASS by design: atomic hold-to-pending publication |
| Final outcomes | PASS: retain terminal decisions | PASS by design: repeated/refused operations preserve state |
| Reliable operations | PASS: existing transactions | PASS by design: existing concurrency regressions retained |
| Simple design | PASS: immutable domain | PASS: no I/O or new domain persistence abstraction |
| Evidence | PASS: measurable criteria | PASS by design: quickstart defines required evidence |
| Workflow | 002 dependency recorded implemented | Existing dirty implementation predates this plan; no retrospective process claim |

These are design gates, not executed implementation checks. No constitutional deviation is proposed.

## Project Structure

```text
specs/005-market-conformance/
  plan.md
  research.md
  data-model.md
  contracts/market.md
  quickstart.md
  execution-handoff.md
rescue/market/models/
  b3_market.py
  named_value.py
  fleet/
  availability/rules/
  procurement/rules/
  quotes/rules/
  offers/rules/
  inventory/rules/
tests/unit/market/<topic>/test_<name>.py
tests/architecture/market_layout/
```

Each entity/status has a file; each public rule has a file and adjacent Markdown document. Category packages export entities and category rules packages export rules. Aggregate imports use models.b3_market. Root facades expose nothing.

## Requirement trace

| Requirement | Design and acceptance |
|---|---|
| FR-001 | Independent accounting oracle after every generated operation, including refusals |
| FR-002 | One history entry for each successful hold, transfer or close; none on refusal |
| FR-003 | Closed string-compatible statuses validated at construction |
| FR-004 | Market-owned protocols, declared import contract, type-only import checks |
| FR-005/005a | Every required docstring individually names diagram and what/when/why; per-rule refusal documentation |
| FR-006 | Mechanical category import migration; no old facades |
| FR-007 | Both UML and ER show six categories, statuses and history, with consistent rendered artifacts |
| FR-008 | Real immutable inputs, no domain fakes or I/O in pure tests; independently require zero missed lines and branches |
| FR-009 | Full suite and byte comparison against committed pre-feature demo baseline |

## Execution preparation

See [execution-handoff.md](execution-handoff.md) for dependencies and [P] ownership. Generate tasks.md through speckit-tasks next; its after_tasks hook owns the bridge handoff. This command ends after Phase 1 and does not execute SDD or implementation.

## Complexity Tracking

No constitutional exception. Cosmic Python and Clean Architecture apply within the existing capability layout. Project-setup informs pins, top-level package, test tiers and enforced boundaries. Repository-wide OpenSpec/Antora adoption or tool-config migration exceeds 005 and the roadmap's conformance-in-place decision.
