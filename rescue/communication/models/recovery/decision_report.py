"""Central's sequenced report of one decision on a ship response, kept for recovery.

What: the immutable outbound report that names the response it decides, its disposition and reason, and its place in the mission's decision order.
When called: built by the application when central commits or rejects a decision on a sequenced response, and retained in the session for replay.
Why: a replayed report must repeat the same identities, numbers and content, so it is a frozen value whose mission order arithmetic is checked when it is built.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import (
    DomainValidationError,
    Id,
    normalize_id,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def _vocabulary[T: (DeliveryDisposition, DeliveryReason)](
    kind: type[T], label: str, value: object
) -> T:
    """Return the closed member named by a value or raise a labelled domain error.

    What: converts a member or its string value and rejects None, blanks and unknown spellings.
    Why: a report that drops its disposition or reason would hide what central decided.
    """
    try:
        return kind(value)
    except ValueError:
        raise DomainValidationError(f"decision report {label} must be a known {label}") from None


@dataclass(frozen=True, slots=True)
class DecisionReport:
    """Central's sequenced account of one decision, replayed unchanged on recovery.

    What: names the report, its outbound envelope, the message and delivery it decides, the mission,
      the disposition and reason, and the mission order numbers before and after the decision.
    When called: created when central decides a sequenced response and read when a ship recovers
      retained reports.
    Why: a mission order number exists only when the decision appended history, and it must be the
      one after the previous number, so a gap or reuse cannot be stored.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    report_id: Id
    envelope: SessionEnvelope
    message_id: Id
    delivery_id: Id
    mission_id: Id | None
    disposition: DeliveryDisposition
    reason: DeliveryReason
    mission_sequence: int | None
    after_mission_sequence: int

    def __post_init__(self) -> None:
        normalize_id(self.report_id)
        if (
            not isinstance(self.envelope, SessionEnvelope)
            or self.envelope.direction is not FlowDirection.OUTBOUND
        ):
            raise DomainValidationError(
                "decision report envelope must be an outbound session envelope"
            )
        normalize_id(self.message_id)
        normalize_id(self.delivery_id)
        if self.mission_id is not None:
            normalize_id(self.mission_id)
        object.__setattr__(
            self, "disposition", _vocabulary(DeliveryDisposition, "disposition", self.disposition)
        )
        object.__setattr__(self, "reason", _vocabulary(DeliveryReason, "reason", self.reason))
        after = normalize_nonnegative_quantity(self.after_mission_sequence)
        if self.mission_sequence is not None:
            normalize_positive_quantity(self.mission_sequence)
        if self.mission_id is None and (self.mission_sequence is not None or after != 0):
            raise DomainValidationError(
                "a report without a mission cannot carry mission order numbers"
            )
        if self.mission_sequence is not None and self.mission_sequence != after + 1:
            raise DomainValidationError(
                "mission_sequence must be None or after_mission_sequence + 1"
            )
