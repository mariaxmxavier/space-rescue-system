"""Comparison service: run each allocator on each scenario and report one metrics row.

Called by the comparison benchmark with an injected clock. It sends every run through the
checked decision path, so allocator rules are enforced and trace logging is kept, and it
reads time only through the injected callable so the service stays pure.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from rescue.mission.models import Mission
from rescue.mobilisation.algorithms import Allocator
from rescue.mobilisation.models import (
    AlgorithmName,
    Candidate,
    DecisionContext,
    MobilisationPolicy,
)
from rescue.mobilisation.models.candidate import arrival_instant
from rescue.mobilisation.services.decide import select_offers

Scenario = tuple[Mission, tuple[Candidate, ...], DecisionContext]


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    """Metrics of one allocator on one scenario.

    Produced once per scenario and algorithm by compare and printed by the benchmark. The
    arrival is measured from the decision time and is None when no ship is chosen.
    """

    scenario: str
    algorithm: AlgorithmName
    seats_covered: int
    last_seat_arrival_s: float | None
    ships_used: int
    unused_seats: int
    runtime_ms: float


def compare(
    scenarios: Mapping[str, Scenario],
    allocators: Mapping[AlgorithmName, Allocator],
    clock: Callable[[], float],
) -> tuple[ComparisonRow, ...]:
    """Return one ComparisonRow per scenario and allocator, scenarios first, in input order.

    Called to compare allocation strategies on the same inputs. The clock returns seconds
    and is read once before and once after each decision, and runtime_ms is the difference.
    """
    rows: list[ComparisonRow] = []
    for name, (mission, candidates, context) in scenarios.items():
        by_ship = {candidate.ship_id: candidate for candidate in candidates}
        for algorithm, allocator in allocators.items():
            policy = MobilisationPolicy(
                policy_id=f"compare-{algorithm.value}",
                revision=1,
                name=algorithm.value,
                selection_criteria=algorithm.value,
            )
            start = clock()
            decision = select_offers(
                mission, candidates, policy, context, allocators={algorithm: allocator}
            )
            end = clock()
            chosen = [item for item in decision.evaluations if item.selected]
            arrivals = [arrival_instant(by_ship[item.ship_id]) for item in chosen]
            rows.append(
                ComparisonRow(
                    scenario=name,
                    algorithm=algorithm,
                    seats_covered=sum(item.proposed_seats for item in chosen),
                    last_seat_arrival_s=max(arrivals) - context.recorded_at if arrivals else None,
                    ships_used=len(chosen),
                    unused_seats=sum(
                        by_ship[item.ship_id].allocatable_seats - item.proposed_seats
                        for item in chosen
                    ),
                    runtime_ms=(end - start) * 1000,
                )
            )
    return tuple(rows)
