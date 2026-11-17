# Subagent-driven delivery: composed timelines

**State**: prepared, not executing. Canonical work: [tasks.md](tasks.md). No product edits or implementation tasks have run.

**Registration**: the mandatory after_tasks handoff was preflighted and deferred because .specify/superpowers-handoff.json is executing specs/013-web-app (39 pending tasks at observation). It has no per-feature output option; overwriting it would steal another session's lifecycle. No shared handoff/snapshots were changed by this feature. After that execution releases the bridge, register 012 explicitly with update-handoff.ps1 -Status ready -FeatureDirectory specs/012-simulations -Actor codex, then enter through the bridge. This local guide is not a claim that global registration succeeded.

## Entry and recovery

Use start-work and the Spec Kit Superpowers bridge with SPECIFY_FEATURE_DIRECTORY set explicitly to specs/012-simulations; the shared feature pointer may still belong to spec013. The actual planning checkout is main, not the future feature workspace. Native Codex workspace isolation is required before product edits. bit is unavailable in this session; this ownership table is the coordination fallback, not an invented bit issue.

The bridge derives a disposable adapter from tasks.md outside .superpowers/sdd/. Create only this adapter's workspace using the SDD skill's sdd-workspace script and its progress.md ledger. Record canonical task IDs, file ownership, interfaces, decisions, baseline/diff package and test evidence. Resume from that ledger; never infer completion from an agent stopping. Do not use another plan's ledger or hand-edit bridge snapshots.

## Ownership and waves

| Wave | Tasks | Writer-owned paths |
|------|-------|--------------------|
| A [P] | T001 | rescue/api/codec.py; tests/integration/api/http/test_nested_commands.py |
| A [P] | T002 | pyproject.toml, uv.lock, Makefile, existing boundary config test; all simulation package skeleton/initializers |
| B | T003 | simulations/models/**; adapters/ports/mission_api.py; shared fake; model tests |
| C [P] | T004 | adapters/http/**; unit adapter tests; integration/simulations/http/** |
| C [P] | T005 | services/run_scenario.py, solver_round.py; unit services tests |
| C [P] | T006 | situations/rescue/**, situations/requests/**; corresponding unit situation tests |
| C [P] | T007 | situations/communication/**; corresponding unit situation tests |
| C [P] | T008 | situations/safety/**, situations/availability/**; corresponding unit situation tests |
| C [P] | T013 | tests/architecture/simulations/** |
| D | T009 | scenarios/all_twelve.py; integration/timeline/test_all_twelve.py |
| E [P] | T010 | scenarios/{eleven,ten,baseline,catalogue}.py; unit scenario tests |
| E [P] | T011 | integration/timeline/{test_variants,test_repeatability}.py |
| F | T012 | entrypoints/**, simulations/__main__.py; unit entrypoint tests |
| G | T014 | e2e/simulations/timeline/**; integration/simulations/cli/** |
| H | T015/T016 parent | docs, shared configuration/exports and final verification |

Paths refer to simulations/ or tests/ as named in tasks.md. All __init__.py files remain parent-owned even inside a worker's subtree; use direct imports until the parent integrates exports. No shared conftest.py edits by parallel writers. A worker must report required contract changes and cannot rewrite frozen models/ports. No nested implementers or reviewers from workers.

## SDD protocol

1. Preflight the canonical spec/plan/tasks for contradictions, confirm T001's runtime codec repair is covered, and record any ruling with its reason and rework cost.
2. Freeze T003 and its test fake before dispatching C. One fresh implementation context per task; bounded briefs point to contract files instead of copying all history. Tell every writer they are not alone and must preserve other edits.
3. The maintainer explicitly authorised parallel [P] work. This overrides the SDD skill's normal prohibition on concurrent implementers only for the nonoverlapping waves above. Dependencies and shared-file ownership remain binding.
4. Use codex-runner for bounded writes and codex-reviewer for read-only reviews when those harness roles are available. If unavailable, use fresh native agents with those explicit scope/read-only constraints; do not claim cross-provider review. Select models at execution time under the SDD skill's role guidance; no unsupported model-family claims.
5. Per-task reviewer receives brief, implementer report and a task-scoped uncommitted diff file. Both spec compliance and quality verdicts are required. Product changes remain uncommitted; adapt any skill's commit-based packaging to recorded base HEAD plus owned-path working-tree diffs.
6. Parent checks evidence and aggregate state before marking a task complete. Resume its original worker for fixes; review the fix diff. Record rulings and parked findings according to SDD, without silently dropping errors.
7. Final fresh reviewer checks the aggregate diff, configuration/contracts, timeline evidence and verification record. Full suite and documented live commands must pass before completion. Do not commit, merge, push, publish or remove worktrees.

## Review-sensitive points

- A complete mission does not end the scenario while events remain; all12 must actually observe all twelve situation IDs in that mission.
- HTTP decisions have evaluations, not a serialized selected property. A proposal commits no seats.
- The known nested decoding defect must be fixed, not patched only in tests.
- Distinguish duplicate message identity from obsolete session sequence; invalid confirmation consumes its inbound sequence.
- Same-time closures precede deliveries. Deferred submission during recovery probes is visible and uses a fresh proposal before final commits.
- Per-run API serialization means concurrent clients do not prove parallel domain transactions.
- Default suite opens no server; explicit live E2E uses a supplied running endpoint. No auto server launch.
