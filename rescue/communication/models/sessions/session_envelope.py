"""The identity of one message in a ship's sequenced session exchange.

What: the session, version, direction and sequence number that a business message carries.
When called: built by the sender when it allocates a sequence number, and read by the receiver to
  decide whether a message is new, a replay or a gap.
Why: a sequence number is only comparable within one session version and direction, so the
  envelope carries all four facts together.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError, Id, normalize_id, normalize_positive_quantity


def _flow_direction(value: object) -> FlowDirection:
    """Return the closed flow direction named by a member or its string value.

    What: converts the raw direction and raises the labelled domain error for any other value.
    Why: a sequence compared across directions would let a replayed message pass as the other way.
    """
    try:
        return FlowDirection(value)
    except ValueError:
        raise DomainValidationError(f"unknown flow direction: {value!r}") from None


@dataclass(frozen=True, slots=True)
class SessionEnvelope:
    """The identity of one message in a ship's sequenced session exchange.

    What: names the session, its version, the flow direction and the message's sequence number.
    When called: built for each business message on a sequenced session and compared by the
      session rules when they classify it.
    Why: sequence numbers only order messages within one session version and direction, so an
      envelope missing any of these would let an old message be mistaken for a new one.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    session_id: Id
    version: int
    direction: FlowDirection
    sequence: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", normalize_id(self.session_id))
        object.__setattr__(self, "version", normalize_positive_quantity(self.version))
        object.__setattr__(self, "direction", _flow_direction(self.direction))
        object.__setattr__(self, "sequence", normalize_positive_quantity(self.sequence))
