# Subagent execution preparation

Preparation for speckit-tasks and its automatic bridge handoff; this is not tasks.md or an active SDD ledger.

## Global constraints

Spec is binding. Preserve dirty work. No commits, pushes, PRs or bridge snapshot edits. Behaviour changes require tasks. Preserve demo bytes except new history; market imports only itself, rescue.values and standard library; 100% market line and branch coverage; no new dependencies.

## Stages and ownership

1. Controller verifies existing linked worktree and baseline, uses start-work before code edits and identifies genuine remaining work.
2. Domain worker owns rescue/market only. Settle entity/rule/category interfaces first.
3. Once interfaces settle, dependency-independent scopes are:
   - [P] Test worker: tests/unit/market only, seeded accounting and refusal coverage with real values.
   - [P] Architecture worker: tests/architecture/market_layout and market contract in pyproject.toml only.
   - [P] Diagram worker: existing ShipMarket diagram directory only, UML/ER and rendered consistency. New flow diagram awaits approval.
4. Integration worker receives an explicit caller/test file list outside those scopes. Outside-market production edits are mechanical import migrations only; assigned integration test files may add atomic publication and rollback regressions. No peer redesign.
5. Controller reviews aggregate diff and verifies full gates, market coverage and demo bytes; reconcile roadmap status with evidence.

For subagent-driven-development, use a fresh implementer per task, independent spec/quality review after each and final whole-branch review. Its sequential writer requirement applies: [P] marks dependency independence, not permission for concurrent SDD writers. Read-only reviews may run concurrently. Briefs contain exclusive paths, constraints and report locations; workers must not revert others' work, commit or spawn their own reviewers.

Create the SDD workspace/ledger only after authoritative tasks and bridge handoff exist. Record verified completion, not agent-stop events. Prefer codex-reviewer when available; this session used read-only default reviewers because the role was unavailable.
