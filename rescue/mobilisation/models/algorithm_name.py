"""AlgorithmName: the closed set of allocation strategies a policy may select.

Read when a policy resolves its strategy and when a decision picks an allocator. A closed
set makes an unknown strategy fail at construction instead of during a decision.
"""

from __future__ import annotations

from enum import StrEnum


class AlgorithmName(StrEnum):
    """The six allocation strategies; each value is the name stored in policy criteria.

    Used by policies, allocation results and the allocator registry so one spelling is
    shared everywhere. Diagram: MobilisationPolicy.selection_criteria.
    """

    EARLIEST_ARRIVAL = "earliest_arrival"
    LARGEST_CAPACITY = "largest_capacity"
    PRIORITY_QUEUE = "priority_queue"
    MIN_COST_FLOW = "min_cost_flow"
    CP_SAT = "cp_sat"
    KNAPSACK = "knapsack"
