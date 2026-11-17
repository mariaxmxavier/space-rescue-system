"""Closed vocabulary of the directions a communication session flows in.

What: the two directions of a session, from ship to central and from central to ship.
When called: carried by SessionEnvelope and SequenceControl; read by recovery and reporting rules.
Why: a closed pair stops a replayed envelope from being read as traffic going the other way.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class FlowDirection(StrEnum):
    """The direction a session message travels.

    What: INBOUND is a ship response to central; OUTBOUND is a central instruction to a ship.
    When called: assigned when a session envelope or sequence control is built for a message.
    Why: inbound is idempotent and outbound is recoverable, so the direction selects the guarantee.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    INBOUND = "inbound"
    OUTBOUND = "outbound"
