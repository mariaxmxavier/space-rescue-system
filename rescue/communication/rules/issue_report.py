"""Issue the next sequenced decision report on a session.

What: builds a decision report on the session's next outbound number and returns the session that retains it.
When called: central calls it after deciding a sequenced response, before the report is sent to the ship.
Why: taking the number and retaining the report in one step keeps retained reports covering exactly the issued numbers, so recovery can replay them.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import Id


def issue_report(
    session: CommunicationSession,
    *,
    report_id: Id,
    message_id: Id,
    delivery_id: Id,
    mission_id: Id | None,
    disposition: DeliveryDisposition,
    reason: DeliveryReason,
    mission_sequence: int | None,
    after_mission_sequence: int,
) -> tuple[CommunicationSession, DecisionReport]:
    """Return the session with the new report retained, and the report itself.

    What: uses the session's next outbound number for the report envelope, appends the report and advances the number by one.
    When called: once per decided sequenced response, with the mission order numbers the decision produced.
    Why: the input session is never changed, so a rejected decision leaves the stored session intact.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    report = DecisionReport(
        report_id=report_id,
        envelope=SessionEnvelope(
            session.session_id, session.version, FlowDirection.OUTBOUND, session.next_outbound
        ),
        message_id=message_id,
        delivery_id=delivery_id,
        mission_id=mission_id,
        disposition=disposition,
        reason=reason,
        mission_sequence=mission_sequence,
        after_mission_sequence=after_mission_sequence,
    )
    updated = replace(
        session, reports=(*session.reports, report), next_outbound=session.next_outbound + 1
    )
    return updated, report
