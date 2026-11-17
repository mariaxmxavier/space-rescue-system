# Roadmap: Per-Package Conformance

Baseline: `001-rescue-domain-model` (merged to `main`).

Goal: bring each package under `rescue/` up to the cosmic-python layer rules and the
project-setup quality gates, one package at a time, without moving packages. The current
domain-first layout stays as it is (decision recorded 2026-11-16).

## Order

| Spec | Scope | Depends on | Branch / worktree | Status |
|------|-------|------------|-------------------|--------|
| 002 | Project foundation: pinned toolchain, one check command, declared import contracts, tests at `tests/<type>/<package>/<topic>/`, docs grouped by kind, CI, agent instructions | 001 | `002-project-foundation` | Implemented |
| 003 | `rescue/adapters/` | 002 | `003-adapters-conformance` | Specified |
| 004 | `rescue/mission/`: invariant table tests, named outcomes | 002 | `004-mission-conformance` | Specified |
| 005 | `rescue/market/`: six categories, one file per entity, named statuses, quote history, generated capacity tests | 002 | `005-market-conformance` | Implemented; final review pending |
| 006 | `rescue/mobilisation/`: strategy tests, declared one-way peers | 002 | `006-mobilisation-conformance` | Specified |
| 007 | `rescue/communication/`: extract delivery classification from central | 002 | `007-communication-conformance` | Specified |
| 008 | `rescue/application/`: one service per use case, break import cycle, move `RunState` inward | 002, 003, 007 | `008-application-conformance` | Specified |
| 009 | `rescue/experiments/`: inject run factory, split pure vs runner | 002, 008 | `009-experiments-conformance` | Specified |
| 010 | Root modules: `values.py` core, `bootstrap.py` + `demo.py` entrypoints, full layer contract | 002, 003, 008, 009 | `010-root-modules-conformance` | Specified |
| 011 | HTTP API (FastAPI) entrypoint over the application services; JSON in/out, browser-callable | 010 | `011-http-api` | Planned |
| 012 | `simulations/`: scripted scenario runs that drive the system through the 011 HTTP API | 011 | `012-simulations` | Planned |
| 013 | Browser app (HTML, CSS, JavaScript) on top of the 011 HTTP API | 011 | `013-web-app` | Planned |

Decisions (2026-11-16): conform in place; ports move to `adapters/` as ABCs (003, option B).
The HTTP API comes after 010 so it is built once on the final application layer (011–013 added 2026-11-16).

Worktrees live under `~/worktrees/github.com/mariaxmxavier/space-rescue-system/<branch>`.

## Rules for every package spec (003 and later)

- Conform in place: fix rule violations inside the package; no cross-package restructure.
- Each package declares its allowed imports as a contract checked by the 002 tooling.
- Each package meets its own layer's coverage target and test style (cosmic-python test table).
- One class or rule per file, in nested folders that mirror the package's UML diagram; every
  module, class and public function has a What / When called / Why / Diagram docstring (set by 004).
- Constitution invariants (seat accounting, final outcomes, reliable operations) stay green
  throughout: the full existing test suite passes on every branch.

## Merge order

002 merges first. 003–007 can merge in any order after 002, but 007 must merge before 008,
because both edit `central.py`. Then 008 → 009 → 010 → 011. 012 and 013 both follow 011 and can
merge in either order. Each branch rebases onto `main` before
`/speckit-plan`.

Known cross-cutting issue: `application.central` → `experiments.runner` (a function-local
import) → `bootstrap` → `application.central` is an import cycle. It is broken by 008 and 009
together.
