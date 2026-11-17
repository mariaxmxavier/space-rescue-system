"""Decide whether an inbound envelope executes, repeats or is stale for its session.

What: applies one inbound SessionEnvelope to the session and returns the new session, any gap notice and a verdict of execute, duplicate or stale.
When called: RescueCentral.record_response calls it after classify_delivery, only for a received
  delivery whose decision records, expires then records or applies it, and before the mission
  step. A lost or already known delivery never reaches it.
Why: one pure step keeps inbound idempotent, lets later responses proceed past a gap and rejects old versions.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def accept_inbound(
    session: CommunicationSession | None, envelope: SessionEnvelope
) -> tuple[CommunicationSession | None, NotApplied | None, str]:
    """Return the session after the envelope, the gap it opened and the verdict.

    What: creates or resets the session for a new or higher version, then compares the sequence
      with next_inbound; lower versions and old sequences leave the session unchanged.
    When called: RescueCentral.record_response calls it once per received delivery whose decision
      records, expires then records or applies it, after classify_delivery and before the mission
      step; an outbound envelope raises DomainValidationError.
    Why: the first-seen number executes once, a skipped range becomes a gap and a replay is ignored.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    if envelope.direction is not FlowDirection.INBOUND:
        raise DomainValidationError("accept_inbound requires an inbound envelope")
    if session is not None and envelope.version < session.version:
        return session, None, "stale"
    if session is None or envelope.version > session.version:
        session = CommunicationSession(envelope.session_id, envelope.version, 1, 1, (), (), None)
    expected = session.next_inbound
    if envelope.sequence < expected:
        return session, None, "duplicate"
    gap = None
    if envelope.sequence > expected:
        gap = NotApplied(
            session.session_id, session.version, expected, envelope.sequence - expected
        )
    gaps = session.gaps + (gap,) if gap else session.gaps
    return replace(session, next_inbound=envelope.sequence + 1, gaps=gaps), gap, "execute"
