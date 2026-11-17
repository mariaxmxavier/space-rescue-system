"""Closed vocabulary of the reasons a communication delivery can record.

What: the fifteen reason labels a delivery attempt carries after the rules classify it.
When called: assigned by the delivery classification rules and stored on the delivery and its decision report.
Why: a closed set keeps every applied, ignored, lost, rejected or late delivery explainable and comparable across reports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class DeliveryReason(StrEnum):
    """The named reason a delivery attempt was applied, ignored, lost, rejected or late.

    What: one value per reason the delivery rules or the mission rules can return for an attempt.
    When called: chosen for each received attempt, then read when central writes the decision report.
    Why: exact labels let tests and reports compare reasons without parsing free text.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    RESPONSE_APPLIED = "response_applied"
    IDENTITY_CONFLICT = "identity_conflict"
    TRANSPORT_LOSS = "transport_loss"
    UNKNOWN_REQUEST = "unknown_request"
    INVALID_INPUT = "invalid_input"
    CLOSED_REQUEST = "closed_request"
    DEADLINE_EXPIRED = "deadline_expired"
    UNKNOWN_MISSION = "unknown_mission"
    UNKNOWN_SHIP = "unknown_ship"
    INSUFFICIENT_DEMAND = "insufficient_demand"
    INSUFFICIENT_CAPACITY = "insufficient_capacity"
    UNAVAILABLE = "unavailable"
    EXPIRED_QUOTE = "expired_quote"
    REVISION_CONFLICT = "revision_conflict"
    DUPLICATE_SEQUENCE = "duplicate_sequence"
