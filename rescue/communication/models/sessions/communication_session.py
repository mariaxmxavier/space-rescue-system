"""One ship's sequenced exchange with central, held as a single immutable value.

What: the active version, the next inbound and outbound numbers, retained reports, gap notices and any outstanding recovery request.
When called: created when the first envelope of a session arrives and replaced by the session rules after each inbound message, report or synchronise.
Why: keeping counters, reports and gaps together lets one constructor check that they agree, so a session that skips or reuses a number cannot be stored.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.values import DomainValidationError, Id, normalize_id, normalize_positive_quantity


def _tuple_of(kind: type, label: str, members: str, value: object) -> tuple:
    """Return the value when it is a tuple of the given kind or raise a labelled domain error.

    What: rejects lists and other containers and any member of the wrong type.
    Why: a mutable or mistyped collection would let the session change after it was checked.
    """
    if not isinstance(value, tuple):
        raise DomainValidationError(f"{label} must be a tuple")
    if not all(isinstance(item, kind) for item in value):
        raise DomainValidationError(f"{label} must hold only {members}")
    return value


@dataclass(frozen=True, slots=True)
class CommunicationSession:
    """One ship's session at its active version, with counters, reports and gaps.

    What: names the session and version, the next inbound and outbound numbers, the retained
      decision reports, the gap notices and at most one outstanding recovery request.
    When called: built by the session rules, which return a new session for each accepted event.
    Why: reports must cover exactly the outbound numbers issued and every part must share the
      session id and version, so the checks live in one place.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    session_id: Id
    version: int
    next_inbound: int
    next_outbound: int
    reports: tuple[DecisionReport, ...]
    gaps: tuple[NotApplied, ...]
    outstanding_recovery: RecoveryRequest | None

    def __post_init__(self) -> None:
        normalize_id(self.session_id)
        normalize_positive_quantity(self.version)
        normalize_positive_quantity(self.next_inbound)
        normalize_positive_quantity(self.next_outbound)
        _tuple_of(DecisionReport, "reports", "decision reports", self.reports)
        _tuple_of(NotApplied, "gaps", "not applied notices", self.gaps)
        if self.outstanding_recovery is not None and not isinstance(
            self.outstanding_recovery, RecoveryRequest
        ):
            raise DomainValidationError("outstanding recovery must be a recovery request")
        key = (self.session_id, self.version)
        if any((r.envelope.session_id, r.envelope.version) != key for r in self.reports):
            raise DomainValidationError("report session and version must match the session")
        if [r.envelope.sequence for r in self.reports] != list(range(1, self.next_outbound)):
            raise DomainValidationError(
                "report outbound sequences must be 1 to next_outbound - 1 in order"
            )
        if any((g.session_id, g.version) != key for g in self.gaps):
            raise DomainValidationError("gap session and version must match the session")
        recovery = self.outstanding_recovery
        if recovery is not None and (recovery.session_id, recovery.version) != key:
            raise DomainValidationError("recovery session and version must match the session")
