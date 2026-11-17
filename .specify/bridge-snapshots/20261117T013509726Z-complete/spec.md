# Feature Specification: Project Foundation

**Feature Branch**: `002-project-foundation`

**Created**: 2026-11-16

**Status**: Draft

**Input**: "Give the repository one health check, declared package boundaries, and a tidy layout for
tests and docs, so each `rescue` package can then be brought to cosmic-python conformance on its own
branch (specs 003–010)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One command says whether the repository is healthy (Priority: P1)

A contributor clones the repository, installs the pinned tools, and runs one check command. It runs
formatting, linting, import rules, and all tests with coverage, and reports a single pass or fail.

**Why this priority**: Specs 003–010 each report "done" against this command.

**Independent Test**: On a fresh clone, install and run the check command; it passes on current
`main` code with no source changes.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the contributor installs, **Then** the interpreter and every
   tool resolve to exact pinned versions recorded in a lock file.
2. **Given** an installed environment, **When** the check command runs, **Then** it reports one
   pass or fail and shows each gate's result.
3. **Given** a change that breaks any gate, **When** the check command runs, **Then** it fails and
   names the gate and the offending file.

---

### User Story 2 - Package boundaries live in one declarations file (Priority: P1)

A maintainer reads one file to see which `rescue` packages may import which; the check command
enforces it.

**Why this priority**: Each package spec adds or tightens its own rule there.

**Independent Test**: Add a forbidden import (a domain package importing `rescue.adapters`); the
check fails naming the rule. Remove it; the check passes.

**Acceptance Scenarios**:

1. **Given** the declared rules, **When** `mission`, `market`, `mobilisation` or `communication`
   imports `rescue.application`, `rescue.adapters` or `rescue.bootstrap`, **Then** the check fails.
2. **Given** the import-only rules in the current architecture test, **When** compared with the
   declared rules, **Then** each one is covered before it is removed from the test.
3. **Given** rules a declaration cannot express (forbidden I/O calls in domain packages), **When**
   the check runs, **Then** the architecture test still enforces them.

---

### User Story 3 - Tests and docs are easy to find (Priority: P1)

A contributor finds every test by what kind of test it is, which package it covers, and which topic
it checks; and finds every document by its kind.

**Why this priority**: Package specs work one package at a time and set per-package coverage; their
tests must already be grouped by package.

**Independent Test**: Run each test type alone and the full suite; all pass, the full count equals
the pre-move count, and coverage is reported per package.

**Acceptance Scenarios**:

1. **Given** the new layout, **When** a contributor looks for a test, **Then** it sits at
   `tests/<type>/<package>/<topic>/`, as mapped in FR-006.
2. **Given** the new layout, **When** a contributor runs one type (for example `unit`), **Then**
   only that type's tests run.
3. **Given** the full suite, **When** it runs, **Then** the test count equals the count before the
   move, and no assertion changed.
4. **Given** the docs, **When** a contributor opens `docs/`, **Then** each document sits under its
   kind (FR-008) and every link in the repository still resolves.

---

### User Story 4 - Every push is checked automatically (Priority: P2)

A reviewer sees the check command's result on every push and pull request.

**Why this priority**: Parallel package branches need one shared gate before merge.

**Independent Test**: Push the branch; automation runs the same check command and reports pass.

**Acceptance Scenarios**:

1. **Given** a push or pull request, **When** automation runs, **Then** it uses the same pinned
   versions and the same check command as a contributor's machine.

### Edge Cases

- `test_concurrency` and `test_timing` use threads and timing; moving them must not change their
  assertions.
- The pinned interpreter (3.14.10) may be missing on the automation host; the run must fail loudly,
  not fall back to another version.
- Test files in different folders may share a base name later; the runner must not confuse them.
- Moving diagrams breaks relative links in `specs/001-*`, the constitution, and the diagram README's
  render commands; all must be updated. Frozen snapshots under `.specify/bridge-snapshots/` are not
  edited.
- `__pycache__` folders must stay out of version control.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The interpreter and every tool MUST be pinned to exact versions in a lock file.
- **FR-002**: One check command MUST run format check, lint, declared import rules, and the full
  test suite with per-package coverage, failing if any gate fails. No coverage minimum is set here.
- **FR-003**: Allowed imports between `rescue` packages MUST be declared in one file and enforced
  by the check command, covering every import-only rule in `test_architecture.py` before that rule
  is removed from the test.
- **FR-004**: Tests MUST live at `tests/<type>/<package>/<topic>/`. Types are `unit` (one pure
  rule, no wiring), `integration` (real parts wired through a run context), `e2e` (the whole system
  driven through its entry point), and `architecture` (structure and boundary checks).
- **FR-005**: Each test type MUST be runnable alone.
- **FR-006**: Existing test files MUST move as follows, with no assertion changed:

  | File | New folder |
  |------|------------|
  | test_mission | `unit/mission/rules/` |
  | test_market | `unit/market/rules/` |
  | test_policies | `unit/mobilisation/policies/` |
  | test_experiments | `unit/experiments/simulation/` |
  | test_experiment_models | `unit/experiments/models/` |
  | test_results | `unit/experiments/results/` |
  | test_timeline | `unit/experiments/timeline/` |
  | test_contracts | `unit/application/contracts/` |
  | test_values | `unit/values/validation/` |
  | test_central | `integration/application/central/` |
  | test_concurrency | `integration/application/concurrency/` |
  | test_resilience | `integration/application/resilience/` |
  | test_communication | `integration/application/communication/` |
  | test_comparison | `integration/application/comparison/` |
  | test_timing | `integration/application/timing/` |
  | test_memory | `integration/adapters/memory/` |
  | test_demo | `e2e/demo/run/` |
  | test_architecture | `architecture/boundaries/` |

- **FR-007**: New tests MUST follow the same `<type>/<package>/<topic>/` rule.
- **FR-008**: Docs MUST be grouped by kind: `docs/context/` (problem statement), `docs/reference/`
  (glossary), `docs/architecture/diagrams/` (all current diagrams), `docs/planning/` (roadmap), with
  `docs/readme.md` as the index. Every repository link to a moved document MUST be updated.
- **FR-009**: Automation MUST run the check command on every push and pull request with the same
  pinned versions.
- **FR-010**: One canonical instructions file MUST describe the check command, the package, test and
  docs layout, the roadmap, and the spec workflow; any agent-specific file MUST only point to it.
- **FR-011**: The README MUST show the new commands; the demo command MUST keep working.
- **FR-012**: Code under `rescue/` MUST NOT change, except behaviour-neutral fixes a gate forces.

### Key Entities

- **Check command**: the single entry point that runs all gates; the done-signal for every roadmap
  spec.
- **Import rule**: a named declaration of which packages may or may not import which.
- **Test location**: type, package and topic, which together fix where a test lives.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a fresh clone, install plus the check command finish with a pass in under 5 minutes
  on a developer laptop.
- **SC-002**: 100% of the import-only rules in the current architecture test map to a declared rule.
- **SC-003**: The full test count after the move equals the count before it.
- **SC-004**: Introducing any single forbidden import fails the check every time (one example per
  declared rule).
- **SC-005**: 100% of test files sit at a `<type>/<package>/<topic>/` path, and 0 repository links
  point to a missing document.
- **SC-006**: Automation shows a pass on the branch's own pull request.

## Assumptions

- Spec Kit (`specs/`, `.specify/`) stays the spec system; no `openspec/` spine is added.
- No deployment: no CD, container image or `infra/` folder.
- The top-level `rescue/` layout (no `src/`) stays.
- Tool choices and exact versions are settled at plan time from current stable releases, including
  whether the test runner changes.
- Out of scope, planned as later specs after 010 (see the roadmap): 011 HTTP API, 012 a
  `simulations/` folder of scripted runs that call that API, 013 an HTML/CSS/JavaScript app on top
  of it.
