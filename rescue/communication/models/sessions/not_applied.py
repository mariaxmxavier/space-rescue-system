"""Notice that inbound sequence numbers were skipped in one ship session.

What: names the session, version and the missing sequence range central did not receive.
When called: created by session rules when an inbound message or synchronise skips numbers.
Why: a visible gap explains a missing response without stopping later valid responses.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, normalize_id, normalize_positive_quantity


@dataclass(frozen=True, slots=True)
class NotApplied:
    """Control notice for a missing inbound sequence range within one session version.

    What: holds the session, the version, the first missing sequence and how many are missing.
    When called: appended to CommunicationSession.gaps when an inbound number skips ahead.
    Why: it is a control, so it consumes no business number and decides no outcome.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    session_id: Id
    version: int
    from_sequence: int
    count: int

    def __post_init__(self) -> None:
        normalize_id(self.session_id)
        normalize_positive_quantity(self.version)
        normalize_positive_quantity(self.from_sequence)
        normalize_positive_quantity(self.count)
