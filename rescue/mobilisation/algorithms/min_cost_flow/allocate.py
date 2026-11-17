"""Min-cost flow allocator: held quotes first, then the rest of the demand as a min-cost flow.

Called through the ALLOCATORS registry when a policy names min_cost_flow. Held quotes are
all-or-nothing, which a flow cannot express, so every eligible quote is decided first, in arrival
order, before any open ship; the residual demand then flows source -> ship -> sink.
"""

from __future__ import annotations

import math

from ortools.graph.python.min_cost_flow import SimpleMinCostFlow

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.candidate import Candidate, arrival_instant
from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import Instant

ALGORITHM = AlgorithmName.MIN_COST_FLOW
SOURCE = 0
SINK = 1
INT64_MAX = 2**63 - 1
USABLE_STATUSES = (SimpleMinCostFlow.OPTIMAL, SimpleMinCostFlow.FEASIBLE)


def _rank_key(candidate: Candidate) -> tuple[object, ...]:
    return (arrival_instant(candidate), candidate.ship_id)


def _arrival_cost(candidate: Candidate, at: Instant) -> int:
    """Whole seconds from decision to arrival, rounded up, never negative."""
    return math.ceil(max(arrival_instant(candidate) - at, 0))


def _quote_seats(candidate: Candidate, remaining: int) -> int:
    offered = candidate.quote.offered_seats
    if remaining <= 0 or offered > remaining or offered > candidate.allocatable_seats:
        return 0
    return offered


def _solve_flow(
    ships: tuple[Candidate, ...], supply: int, at: Instant, trace: list[TraceStep]
) -> dict[str, int]:
    solver = SimpleMinCostFlow()
    solver.set_node_supply(SOURCE, supply)
    solver.set_node_supply(SINK, -supply)
    arcs = []
    for position, ship in enumerate(ships):
        node = position + 2
        arrival_cost = _arrival_cost(ship, at)
        # Scaling by the ship count keeps arrival dominant and breaks ties by (arrival, ship_id).
        unit_cost = min(arrival_cost * len(ships) + position, INT64_MAX)
        solver.add_arc_with_capacity_and_unit_cost(SOURCE, node, ship.allocatable_seats, 0)
        arcs.append(solver.add_arc_with_capacity_and_unit_cost(node, SINK, supply, unit_cost))
        trace.append(
            TraceStep(
                ALGORITHM,
                "arc",
                ship.ship_id,
                (
                    ("capacity", str(ship.allocatable_seats)),
                    ("arrival_cost_s", str(arrival_cost)),
                    ("unit_cost", str(unit_cost)),
                ),
            )
        )
    trace.append(
        TraceStep(ALGORITHM, "model", None, (("ships", str(len(ships))), ("supply", str(supply))))
    )
    status = solver.solve_max_flow_with_min_cost()
    trace.append(TraceStep(ALGORITHM, "status", None, (("status", status.name),)))
    if status not in USABLE_STATUSES:
        return {}
    return {ship.ship_id: solver.flow(arc) for ship, arc in zip(ships, arcs, strict=True)}


def allocate(candidates: tuple[Candidate, ...], demand: int, at: Instant) -> AllocationResult:
    """Allocate held quotes greedily by arrival, then the rest as a min-cost max flow.

    Called by the decision service for the min_cost_flow strategy. Any solver status other
    than OPTIMAL or FEASIBLE gives the flow ships no seats, so the quotes still stand.
    """
    ordered = tuple(sorted(candidates, key=_rank_key))
    trace = [
        TraceStep(
            ALGORITHM, "inputs", None, (("candidates", str(len(ordered))), ("demand", str(demand)))
        )
    ]
    usable = tuple(c for c in ordered if static_skip_reason(c, at) is None)
    seats: dict[str, int] = {}
    remaining = demand
    for candidate in (c for c in usable if c.quote is not None):
        seats[candidate.ship_id] = _quote_seats(candidate, remaining)
        remaining -= seats[candidate.ship_id]
        trace.append(
            TraceStep(
                ALGORITHM,
                "quote",
                candidate.ship_id,
                (
                    ("offered", str(candidate.quote.offered_seats)),
                    ("seats", str(seats[candidate.ship_id])),
                ),
            )
        )
    flow_ships = tuple(c for c in usable if c.quote is None and c.allocatable_seats > 0)
    seats |= _solve_flow(flow_ships, remaining, at, trace)
    chosen = [c for c in ordered if seats.get(c.ship_id, 0) > 0]
    unchosen = [c for c in ordered if seats.get(c.ship_id, 0) == 0]
    for candidate in chosen:
        trace.append(
            TraceStep(
                ALGORITHM, "pick", candidate.ship_id, (("seats", str(seats[candidate.ship_id])),)
            )
        )
    for candidate in unchosen:
        reason = static_skip_reason(candidate, at) or SkipReason.NOT_CHOSEN
        trace.append(TraceStep(ALGORITHM, "skip", candidate.ship_id, (("reason", str(reason)),)))
    covered = sum(seats.values())
    trace.append(
        TraceStep(
            ALGORITHM,
            "result",
            None,
            (("seats", str(covered)), ("remaining_demand", str(demand - covered))),
        )
    )
    return AllocationResult(
        algorithm=ALGORITHM,
        allocations=tuple(
            Allocation(ship_id=c.ship_id, seats=seats.get(c.ship_id, 0)) for c in chosen + unchosen
        ),
        trace=tuple(trace),
    )
