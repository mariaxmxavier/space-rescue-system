# Feature Specification: Mobilisation Conformance

**Feature Branch**: `006-mobilisation-conformance` · **Created**: 2026-11-16 · **Updated**: 2026-11-17 · **Status**: Draft

## Why

Mobilisation answers one question: *which ships do we ask for seats, and how many from each, so
the stranded people are covered?* Today one function both picks the ships (the algorithm) and
records why (the decision). The two are tangled, the choice of algorithm is a free string, and
nobody can say whether the current rule is a good one. This spec separates them, adds the
algorithms most used for this kind of problem, and measures them side by side.

## Scope

In: `rescue/mobilisation/` only, plus its docs and tests.
Out: other packages (they have their own specs, 004, 005, 007); allocating across several missions at once.

## User Stories

### US1 - A reader understands each part from its own file (P1)

A maintainer opens `rescue/mobilisation/` and finds one entity per file, matching the
Mobilisation class and ER diagrams. Every module, class and function says what it does, when it
is called, and why it exists.

**Acceptance**
1. Each entity in the Mobilisation diagrams has its own file, and each file names the diagram it implements.
2. Every module, class and public function has a docstring covering what, when, and why.

### US2 - The decision does not depend on which algorithm chose (P1)

The decision step validates the input, asks the configured algorithm for an allocation, then
records each ship as selected or skipped with a reason. Every algorithm answers through the same
interface.

**Acceptance**
1. Swapping the algorithm in the policy changes the allocation, never the decision's shape or its skip reasons.
2. With the default algorithm, the demo output is byte-identical to today's.
3. An unknown algorithm name is rejected when the policy is built.

### US3 - Five algorithms can be compared on the same scenarios (P2)

Each algorithm lives in its own folder with a README explaining how it works, a worked example,
and its time complexity:

| Algorithm | Idea |
|---|---|
| Greedy, earliest arrival first (default) | Sort by arrival, take `min(seats, remaining demand)` from each |
| Priority queue (min-heap) | Same choice as greedy, kept ordered as ship availability changes |
| Minimum-cost flow | Seats flow from ships to the mission; cost grows with arrival time |
| Integer optimisation (CP-SAT) | Choose ships and quantities under constraints, minimising the last arrival |
| 0/1 knapsack | Whole-ship choices only: take a ship's full offer or none of it |

A comparison runs all five on the same scenarios and reports, for each: arrival of the last
needed seat, ships used, unused seats, and run time.

**Acceptance**
1. Given the same scenario, every algorithm's allocation covers at most the unmet demand and never exceeds a ship's allocatable seats.
2. The comparison prints one row per algorithm per scenario with the four measures.

### US4 - The choice of algorithms is recorded (P2)

A decision record explains why these five were chosen, what each trades off, and which is the
default. A research note lists the sources consulted.

## Edge Cases

- No ship can help: the decision is empty and every ship carries a skip reason.
- Demand already covered: no new requests.
- A ship with zero allocatable seats is skipped, never selected with quantity 0.
- A ship with a held quote is all-or-nothing: its quoted seats are taken whole or not at all.
- Ties (same arrival, same seats) break deterministically by ship id, in every algorithm.
- The knapsack cannot split a ship's offer, so it may cover less demand than the others; that is reported, not hidden.

## Requirements

- **FR-001**: One entity per file under the mobilisation models, matching the Mobilisation diagrams.
- **FR-002**: Every module, class and public function MUST have a what/when/why docstring.
- **FR-003**: The decision step MUST be separate from the allocation algorithm; all algorithms share one interface.
- **FR-004**: The policy MUST name its algorithm from a closed set; the default MUST reproduce today's behaviour.
- **FR-005**: Each of the five algorithms MUST live in its own folder with a README (how it works, example, time complexity).
- **FR-006**: No allocation may exceed unmet demand or a ship's allocatable seats; tests assert this for every algorithm.
- **FR-007**: Mobilisation may import only mission, market, shared values, the standard library and the optimisation library; mission and market MUST NOT import mobilisation. Both rules are checked contracts.
- **FR-008**: A comparison MUST report last-seat arrival, ships used, unused seats and run time per algorithm.
- **FR-009**: A decision record and a research note MUST exist and be linked from the docs index.
- **FR-010**: The full test suite passes and the demo output is unchanged.

## Key Entities

- **MobilisationPolicy**: names the algorithm to use (closed set) and its revision.
- **Candidate**: one ship's current offer, with its allocatable seats and optional held quote.
- **Allocation**: an algorithm's answer for one ship: how many seats to request.
- **OfferEvaluation**: one ship's line in a decision: rank, seats proposed, selected or skipped with reason.
- **MobilisationDecision**: all evaluations for one mission at one moment, under one policy revision.

## Success Criteria

- **SC-001**: 100% of diagram entities map to exactly one file.
- **SC-002**: 5 of 5 algorithms pass the shared allocation tests.
- **SC-003**: The comparison runs every algorithm on every scenario and reports all four measures.
- **SC-004**: Each import contract fails on one seeded violation.
- **SC-005**: 100% line and branch coverage for `rescue/mobilisation/`.
- **SC-006**: Demo output byte-identical; full suite green.

## Assumptions

- The interface is per mission. Minimum-cost flow could serve several missions at once; that
  stays out of scope (the constitution excludes fleet-wide optimisation).
- The existing `largest_capacity` strategy stays available so the demo's policy comparison keeps working.
- The optimisation library is a pinned runtime dependency; it does no I/O, so domain rules still hold.
- Depends on 002. Rebase onto 004/005 if they rename shared vocabulary first.
