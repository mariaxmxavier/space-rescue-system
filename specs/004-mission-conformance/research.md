# Research: Mission Conformance

No `NEEDS CLARIFICATION` remained in the Technical Context. Each item below is a design choice the
spec left to the plan.

## R1. How the closed vocabularies are coded

- **Decision**: `enum.StrEnum` (stdlib, Python ≥ 3.11) for `RequestOutcome`, `ProgressStatus`,
  `HistoryAction`. Models normalise incoming strings with `RequestOutcome(value)` in
  `__post_init__`, so a bad name raises `ValueError` → re-raised as `DomainValidationError`.
- **Rationale**: a `StrEnum` member *is* a `str`: it compares equal to `"accepted"`, formats as
  `accepted` in f-strings and `str()`, and hashes the same. Stored values, rendered demo text and
  any remaining string comparison keep working, which keeps behaviour unchanged (FR-010).
- **Alternatives**: `Literal[...]` types (no runtime closure, fails FR-005 "rejected at
  construction"); module constants (still free strings, no closed set); plain `Enum` (breaks
  equality with stored strings and changes rendered text).
- **Watch**: `repr()` of a member differs (`<RequestOutcome.ACCEPTED: 'accepted'>`). `rescue/demo.py`
  uses no `!r` on these values; the byte-identical demo diff (wave 7) is the proof.

## R2. Which literals outside mission are swapped

- **Decision**: only comparisons and constructions where the value is a mission outcome, progress
  status or history action: reads of `SeatRequest.outcome`, `MissionProgress.status`,
  `RequestHistoryEntry.action`, and arguments passed to `apply_outcome(..., outcome=...)`.
- **Rationale**: the same words belong to other vocabularies: RFQ status `"pending"`/`"expired"`,
  quote status `"accepted"`/`"rejected"`/`"expired"` in `rescue/market/models.py` and
  `rescue/market/rules.py`. Those are market's vocabulary (spec 005), not mission's.
- **Caller files** (comparison sites found by grep): `application/central.py`,
  `application/contracts.py`, `demo.py`, `experiments/models.py`, `experiments/results.py`,
  `experiments/runner.py`, `market/rules.py` (only `request.outcome` reads, lines ≈85–87),
  `market/models.py` (check: likely market-only, no change), `mobilisation/policies.py`.
- **Alternatives**: global replace of every matching literal (would wrongly retype market
  statuses).

## R3. Where private helpers live and how they are named

- **Decision**: `models/_validation.py` holds `normalize_name`, `optional_id`, `optional_instant`,
  and `signed_quantity`. `rules/_accounting.py` holds `account` and `append_history`. Names drop the
  leading underscore inside a private module.
- **Decimal wrapper (FR-006)**: removed. `rescue.values.normalize_instant` already returns an
  identical Decimal for Decimal input. Checked on `-0`, a 29-digit value, `"1.50"`, `7` and `"7"`:
  the shared function and the former wrapper gave the same results, and the parity harness found no
  difference across 75,187 generated cases. The mission models import the shared function directly.
- **Rationale**: clarified in spec session 2026-11-16 (Q1 → A).

## R4. How "one public name per file" and docstrings are enforced

- **Decision**: architecture tests using `ast` (stdlib), under `tests/architecture/mission_layout/`:
  - every non-`__init__`, non-underscore module in `rescue/mission/` defines exactly one public
    top-level class or function (enums all live in `vocabulary.py`, which is the one listed
    exception: one module = one vocabulary);
  - every module, class and public function docstring contains the lines `What:`, `When called:`,
    `Why:`, `Diagram:`; private helpers need `What:` and `Why:`; every `Diagram:` path exists.
- **Alternatives**: ruff `D` (pydocstyle) rules only check presence and style, not the four parts;
  kept off to avoid churn in other packages.

## R5. How code ↔ diagram agreement is enforced

- **Decision**: `test_diagrams_match_code.py` parses each of the 8 `.mmd` files: class-diagram
  boxes (`class Name {` … `-type field`) and ER entity blocks (`Name {` … `type field`). For every
  mission class present, its field-name set must equal the dataclass field set. Relationships are
  reviewed by hand (listed in data-model.md).
- **Rationale**: field drift is the common failure; a 40-line parser catches it on every run.
- **Alternatives**: generate diagrams from code (bigger tool, rejected by Simple Design).

## R6. Diagram rendering

- **Decision**: `mmdc` 11.17.0 with the existing ELK front-matter, `-w 2400`, one command per file
  as listed in `docs/architecture/diagrams/rescue-domain-model/README.md` (Source and rendering).
- **Rationale**: matches how the current SVGs were produced; no new tool.

## R7. Import contracts added

- **Decision**: two import-linter contracts in `pyproject.toml`:
  1. `mission-isolated` (forbidden): `rescue.mission` must not import `rescue.market`,
     `rescue.mobilisation`, `rescue.communication`, `rescue.experiments`, `rescue.application`,
     `rescue.adapters`, `rescue.bootstrap`, `rescue.demo`.
  2. `mission-layers` (layers): `rescue.mission.rules` above `rescue.mission.models`.
- **Coverage gate**: the Makefile's `rescue/mission` report gets `--fail-under=100` (FR-009).
- **Rationale**: FR-008 and the clean-architecture rule "enforce boundaries in code, not diagrams".

## R8. Parallel dispatch safety

- **Decision**: waves (plan.md). Wave 1 (one agent) runs `git mv rescue/mission/models.py
  rescue/mission/models/_legacy.py` (same for `rules.py`) and makes each package `__init__.py`
  re-export from `_legacy`. Waves 2–3 add new files beside `_legacy.py` without touching it or the
  `__init__`s. Wave 4 (one agent) points the `__init__`s at the new files and deletes `_legacy.py`.
- **Rationale**: Constitution, Development Workflow: "Parallel writers MUST have non-overlapping
  file ownership." A module `models.py` and a package `models/` cannot coexist cleanly (the package
  wins), so the move happens first, once. New files never get renamed, so their imports are final
  from the start, and the suite stays green after every wave.
