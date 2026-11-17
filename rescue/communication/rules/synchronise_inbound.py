"""Move a session's inbound expectation forward to the number a ship control reports.

What: checks one inbound SequenceControl against a session and returns the advanced session and the gap notice, or a refusal.
When called: central calls it when a ship tells it which inbound sequence it will send next.
Why: advancing records the skipped numbers as a visible gap while equal is a no-op and a rewind is refused, so earlier acceptances are never reopened.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.models.vocabulary.recovery_rejection import RecoveryRejection
from rescue.values import DomainValidationError


def synchronise_inbound(
    session: CommunicationSession, control: SequenceControl
) -> tuple[CommunicationSession, NotApplied | None] | RecoveryRejection:
    """Return the session advanced to the control, or the reason it was refused.

    What: first match wins: version mismatch is STALE_SESSION, an outbound control raises
      DomainValidationError, a higher next sequence appends NotApplied and sets next_inbound,
      an equal one changes nothing and a lower one is SEQUENCE_REWIND.
    When called: once per inbound synchronise control, before any state is stored.
    Why: refusals return before any change, so counters and reports stay as they were.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    if control.version != session.version:
        return RecoveryRejection.STALE_SESSION
    if control.direction is not FlowDirection.INBOUND:
        raise DomainValidationError("synchronise requires an inbound control")
    expected = session.next_inbound
    if control.next_sequence < expected:
        return RecoveryRejection.SEQUENCE_REWIND
    if control.next_sequence == expected:
        return session, None
    notice = NotApplied(
        session.session_id, session.version, expected, control.next_sequence - expected
    )
    return replace(
        session, next_inbound=control.next_sequence, gaps=(*session.gaps, notice)
    ), notice
