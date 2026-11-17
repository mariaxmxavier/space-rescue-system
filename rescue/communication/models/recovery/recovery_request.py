"""A ship's request to replay retained decision reports from one session version.

What: names the session, version, first sequence and count a ship asks central to resend.
When called: built by the ship when it is missing reports, then passed to recover_reports.
Why: the request is a plain value, so an out-of-range count is still representable and is refused
  by the rule without changing session state.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import DomainValidationError, Id, normalize_id, normalize_positive_quantity


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    """A ship's request to replay retained decision reports from one session version.

    What: one recovery ask naming the session, version, first sequence and count to resend.
    When called: built by the ship when it is missing reports, then passed to recover_reports,
      which checks the 1 to 1000 count bound and the retained range.
    Why: the bound is enforced by the rule rather than here, so a request above it can be
      represented and refused, and the refusal leaves the session unchanged.
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
        if type(self.count) is not int:
            raise DomainValidationError("count must be an integer")
