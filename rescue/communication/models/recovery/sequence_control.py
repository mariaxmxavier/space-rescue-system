"""A session position marker that recovery sends without consuming a business number.

What: the session, version, direction and next sequence that one control reports.
When called: built by the recovery rules to end an outbound replay or to ask an inbound
  session to synchronise.
Why: a control restates where a session stands without consuming a sequence, and checking its
  version and direction stops a stale or opposite-direction control being read as traffic.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError, Id, normalize_id


def _positive_integer(value: object, label: str) -> int:
    """Return a positive integer unchanged or raise a labelled domain error.

    What: accepts only an exact int greater than zero, rejecting booleans and floats.
    Why: a version or sequence of zero, or a bool posing as one, would make the session position
      ambiguous.
    """
    if type(value) is not int or value <= 0:
        raise DomainValidationError(f"{label} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class SequenceControl:
    """A session position marker that recovery sends without consuming a business number.

    What: the session, version, direction and next sequence that one control reports.
    When called: built by the recovery rules to end an outbound replay or to ask an inbound
      session to synchronise.
    Why: a control restates where a session stands without consuming a sequence, and checking its
      version and direction stops a stale or opposite-direction control being read as traffic.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    session_id: Id
    version: int
    direction: FlowDirection
    next_sequence: int

    def __post_init__(self) -> None:
        session_id = normalize_id(self.session_id)
        version = _positive_integer(self.version, "version")
        try:
            direction = FlowDirection(self.direction)
        except ValueError:
            raise DomainValidationError(f"unknown flow direction: {self.direction!r}") from None
        next_sequence = _positive_integer(self.next_sequence, "next_sequence")

        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "next_sequence", next_sequence)
