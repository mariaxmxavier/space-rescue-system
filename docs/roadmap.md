# Roadmap: Per-Package Conformance

Baseline: `001-rescue-domain-model` (merged to `main`).

Goal: bring each package under `rescue/` up to the cosmic-python layer rules and the
project-setup quality gates, one package at a time, without moving packages. The current
domain-first layout stays as it is (decision recorded 2026-11-16).

## Order

| Spec | Scope | Depends on | Branch / worktree | Status |
|------|-------|------------|-------------------|--------|
| 002 | Project foundation: pinned toolchain, one check command, declared import contracts, test tiers, CI, agent instructions | 001 | `002-project-foundation` | Specified |
| 003 | `rescue/adapters/` | 002 | `003-adapters-conformance` | Specified |
| 004 | `rescue/mission/`: invariant table tests, named outcomes | 002 | `004-mission-conformance` | Specified |
| 005 | `rescue/market/`: generated capacity tests, drop mission type ref | 002 | `005-market-conformance` | Specified |
| 006 | `rescue/mobilisation/`: strategy tests, declared one-way peers | 002 | `006-mobilisation-conformance` | Specified |
| 007 | `rescue/communication/`: extract delivery classification from central | 002 | `007-communication-conformance` | Specified |
| 008 | `rescue/application/`: one service per use case, break import cycle, move `RunState` inward | 002, 003, 007 | `008-application-conformance` | Specified |
| 009 | `rescue/experiments/`: inject run factory, split pure vs runner | 002, 008 | `009-experiments-conformance` | Specified |
| 010 | Root modules: `values.py` core, `bootstrap.py` + `demo.py` entrypoints, full layer contract | 002, 003, 008, 009 | `010-root-modules-conformance` | Specified |

Decisions (2026-11-16): conform in place; ports move to `adapters/` as ABCs (003, option B).

Worktrees live under `~/worktrees/github.com/mariaxmxavier/space-rescue-system/<branch>`.

## Rules for every package spec (003 and later)

- Conform in place: fix rule violations inside the package; no cross-package restructure.
- Each package declares its allowed imports as a contract checked by the 002 tooling.
- Each package meets its own layer's coverage target and test style (cosmic-python test table).
- Constitution invariants (seat accounting, final outcomes, reliable operations) stay green
  throughout: the full existing test suite passes on every branch.

## Merge order

002 merges first. 003–007 can merge in any order after 002, but 007 must merge before 008,
because both edit `central.py`. Then 008 → 009 → 010. Each branch rebases onto `main` before
`/speckit-plan`.

Known cross-cutting issue: `application.central` → `experiments.runner` (a function-local
import) → `bootstrap` → `application.central` is an import cycle. It is broken by 008 and 009
together.
