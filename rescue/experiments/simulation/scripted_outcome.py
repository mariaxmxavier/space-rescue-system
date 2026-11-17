"""Resolve a scripted response rule into an outcome and a seat count.

What: `scripted_outcome` maps a rule and the requested seats to (outcome, confirmed seats).
When called: by `schedule_response` once per scheduled response.
Why: the rule may leave seats open, so one place applies it and draws from the run's random source.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

import random

from rescue.experiments.models import ScriptedResponse
from rescue.mission.models import RequestOutcome


def scripted_outcome(
    rule: ScriptedResponse,
    request_seats: int,
    rng: random.Random,
) -> tuple[RequestOutcome, int]:
    """Resolve a scripted response rule into an outcome and a seat count.

    What: refuses, accepts all seats, or confirms a partial count, drawing from `rng` only for an
      unspecified partial with more than one seat requested.
    When called: by `schedule_response` for each scheduled response.
    Why: the rule may omit seats, so the outcome and count are settled in one place.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    if rule.outcome == RequestOutcome.REFUSED:
        return RequestOutcome.REFUSED, 0
    specified = rule.confirmed_seats
    if specified is None:
        if rule.outcome == RequestOutcome.ACCEPTED:
            return RequestOutcome.ACCEPTED, request_seats
        if request_seats <= 1:
            return RequestOutcome.REFUSED, 0
        return RequestOutcome.PARTIALLY_ACCEPTED, rng.randint(1, request_seats - 1)
    confirmed = min(specified, request_seats)
    if confirmed <= 0:
        return RequestOutcome.REFUSED, 0
    if confirmed == request_seats:
        return RequestOutcome.ACCEPTED, request_seats
    return RequestOutcome.PARTIALLY_ACCEPTED, confirmed
