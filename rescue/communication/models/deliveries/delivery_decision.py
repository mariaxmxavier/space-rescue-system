"""The outcome the delivery rules choose for one received ship response.

What: an immutable decision naming what to record, what to do to the mission and what result to report.
When called: returned by the delivery classification rules, then carried out by the application.
Why: classification stays a pure rule while the application alone mutates the mission.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.values import DomainValidationError

ACTIONS = frozenset({"none", "record", "expire_then_record", "apply"})
RESULT_STATUSES = frozenset({"applied", "ignored", "rejected"})
LATE = "late"


@dataclass(frozen=True, slots=True)
class DeliveryDecision:
    """What the application must do for one received response, and what to report.

    What: holds the disposition and reason to record, the action, and the result status and reason.
    When called: built by the delivery rules for every received attempt, including ones recording nothing.
    Why: disposition and reason are absent exactly when the action is none, so no half-recorded row exists.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    disposition: DeliveryDisposition | None
    reason: DeliveryReason | None
    action: str
    result_status: str
    result_reason: str | None

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise DomainValidationError(f"unknown delivery action: {self.action!r}")
        recorded = self.action != "none"
        if (self.disposition is not None) != recorded or (self.reason is not None) != recorded:
            raise DomainValidationError(
                "disposition and reason are set exactly when the action records something"
            )
        if self.result_status not in RESULT_STATUSES:
            raise DomainValidationError(f"unknown result status: {self.result_status!r}")
        if self.result_reason is not None and self.result_reason != LATE:
            try:
                DeliveryReason(self.result_reason)
            except ValueError as error:
                raise DomainValidationError(
                    f"unknown result reason: {self.result_reason!r}"
                ) from error
