"""What: one finite response rule for a ship's one-based request ordinal.
When called: a scenario is built with its response rules.
Why: scripted answers make runs deterministic and repeatable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models import RequestOutcome
from rescue.values import (
    DomainValidationError,
    normalize_id,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class ScriptedResponse:
    """What: one finite response rule for a ship's one-based request ordinal.
    When called: a scenario is built with its response rules.
    Why: scripted answers make runs deterministic and repeatable.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    ship_id: str
    request_ordinal: int
    outcome: str
    confirmed_seats: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        object.__setattr__(
            self, "request_ordinal", normalize_positive_quantity(self.request_ordinal)
        )
        if self.outcome not in {
            RequestOutcome.ACCEPTED,
            RequestOutcome.PARTIALLY_ACCEPTED,
            RequestOutcome.REFUSED,
        }:
            raise DomainValidationError("scripted response has an unsupported outcome")
        if self.confirmed_seats is not None:
            object.__setattr__(
                self,
                "confirmed_seats",
                normalize_nonnegative_quantity(self.confirmed_seats),
            )
        if self.outcome == RequestOutcome.REFUSED and self.confirmed_seats not in (None, 0):
            raise DomainValidationError("refused scripted responses cannot confirm seats")
        if self.outcome == RequestOutcome.PARTIALLY_ACCEPTED and self.confirmed_seats == 0:
            raise DomainValidationError("partial scripted responses require confirmed seats")
