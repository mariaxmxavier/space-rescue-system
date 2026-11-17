"""Compare allocation algorithms on five fixed five-ship scenarios and print a table.

Run as `python -m benchmarks.mobilisation.compare [--trace]`. It exists so the algorithm
families can be judged side by side; it injects the real clock into the pure comparison
service and configures logging only here, never at import time.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Sequence

from rescue.market.models import RFQOffer, ShipOfferRevision
from rescue.mission.models import Mission
from rescue.mobilisation.algorithms import ALLOCATORS
from rescue.mobilisation.models import AlgorithmName, Candidate, DecisionContext
from rescue.mobilisation.services.compare import ComparisonRow, Scenario, compare

DEFAULT_ALGORITHMS = (
    AlgorithmName.EARLIEST_ARRIVAL,
    AlgorithmName.PRIORITY_QUEUE,
    AlgorithmName.MIN_COST_FLOW,
    AlgorithmName.CP_SAT,
    AlgorithmName.KNAPSACK,
)
COLUMNS = (
    "scenario",
    "algorithm",
    "seats_covered",
    "last_seat_arrival_s",
    "ships_used",
    "unused_seats",
    "runtime_ms",
)
DECISION_TIME = 0


def _scenario(
    name: str, demand: int, ships: Sequence[tuple[str, int, int, int | None]]
) -> tuple[str, Scenario]:
    """Build one scenario from (ship, capacity, arrival seconds, held quote seats or None)."""
    candidates = tuple(
        Candidate(
            ship_id=ship_id,
            revision=ShipOfferRevision(
                revision_id=f"{name}-{ship_id}-r",
                revision_number=1,
                capacity=capacity,
                arrival_estimate_seconds=arrival,
                available=True,
                recorded_at=DECISION_TIME,
            ),
            free_seats=capacity,
            quote=None
            if quoted is None
            else RFQOffer(
                offer_id=f"{name}-{ship_id}-q",
                rfq_id=f"{name}-rfq",
                offered_seats=quoted,
                arrival_estimate_seconds=arrival,
                expires_at=1000,
                recorded_at=DECISION_TIME,
                status="held",
            ),
        )
        for ship_id, capacity, arrival, quoted in ships
    )
    mission = Mission(
        mission_id=f"{name}-mission",
        station_name="Benchmark Station",
        people_count=demand,
        created_at=DECISION_TIME,
    )
    context = DecisionContext(
        decision_id=f"{name}-decision",
        recorded_at=DECISION_TIME,
        evaluation_ids=tuple(f"{name}-eval-{index}" for index in range(1, len(candidates) + 1)),
    )
    return name, (mission, candidates, context)


def build_scenarios() -> dict[str, Scenario]:
    """Return the five fixed scenarios, each with five ships and no randomness."""
    return dict(
        (
            _scenario(
                "splittable_demand",
                12,
                (
                    ("ship-1", 5, 10, None),
                    ("ship-2", 5, 20, None),
                    ("ship-3", 5, 30, None),
                    ("ship-4", 5, 40, None),
                    ("ship-5", 5, 50, None),
                ),
            ),
            _scenario(
                "tied_arrivals",
                8,
                tuple((f"ship-{index}", 4, 20, None) for index in range(1, 6)),
            ),
            _scenario(
                "held_quotes",
                9,
                (
                    ("ship-1", 6, 10, 4),
                    ("ship-2", 5, 15, 5),
                    ("ship-3", 4, 20, None),
                    ("ship-4", 6, 30, None),
                    ("ship-5", 3, 40, None),
                ),
            ),
            _scenario(
                "insufficient_supply",
                30,
                (
                    ("ship-1", 4, 10, None),
                    ("ship-2", 3, 20, None),
                    ("ship-3", 5, 30, None),
                    ("ship-4", 2, 40, None),
                    ("ship-5", 6, 50, None),
                ),
            ),
            _scenario(
                "knapsack_undercoverage",
                7,
                tuple((f"ship-{index}", 5, index * 10, None) for index in range(1, 6)),
            ),
        )
    )


class JsonLinesFormatter(logging.Formatter):
    """Format a trace record as one JSON object with algorithm, step, ship_id and detail."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the trace fields of the record as a single JSON line."""
        return json.dumps(
            {
                "algorithm": record.algorithm,
                "step": record.step,
                "ship_id": record.ship_id,
                "detail": record.detail,
            },
            default=str,
        )


def _format_table(rows: Sequence[ComparisonRow]) -> str:
    """Render rows as columns separated by at least two spaces."""
    cells = [COLUMNS] + [
        (
            row.scenario,
            row.algorithm.value,
            str(row.seats_covered),
            "-" if row.last_seat_arrival_s is None else f"{row.last_seat_arrival_s:g}",
            str(row.ships_used),
            str(row.unused_seats),
            f"{row.runtime_ms:.3f}",
        )
        for row in rows
    ]
    widths = [max(len(line[index]) for line in cells) for index in range(len(COLUMNS))]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip() for line in cells
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the comparison, optionally printing allocator trace lines first, and return 0."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--trace" in arguments:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLinesFormatter())
        logger = logging.getLogger("rescue.mobilisation")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    rows = compare(
        build_scenarios(),
        {algorithm: ALLOCATORS[algorithm] for algorithm in DEFAULT_ALGORITHMS},
        time.perf_counter,
    )
    print(_format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
