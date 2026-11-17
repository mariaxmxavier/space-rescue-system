"""Replay retained decision reports to a ship, or refuse the request without changing the session.

What: checks a recovery request against the session and returns the requested reports followed by a sequence control, or a named rejection.
When called: by the application when a ship asks central to resend decision reports it missed.
Why: replaying the original report objects keeps recovered content identical, and refusing first leaves counters and reports unchanged (Constitution III).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.models.vocabulary.recovery_rejection import RecoveryRejection

_MAX_COUNT = 1000


def recover_reports(
    session: CommunicationSession, request: RecoveryRequest
) -> tuple[DecisionReport | SequenceControl, ...] | RecoveryRejection:
    """Return the requested retained reports and a closing control, or the first rejection.

    What: refuses a stale version, an outstanding recovery, a count outside 1 to 1000 or a range
      beyond the issued reports, in that order; otherwise returns the original reports in
      sequence order followed by an outbound control at the next outbound number.
    When called: by the application on a ship's recovery request, before any state is stored.
    Why: the session is only read, so a refusal or a replay never changes counters or reports.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    if request.version != session.version:
        return RecoveryRejection.STALE_SESSION
    if session.outstanding_recovery is not None:
        return RecoveryRejection.RECOVERY_IN_PROGRESS
    if not 1 <= request.count <= _MAX_COUNT:
        return RecoveryRejection.RECOVERY_LIMIT
    last = request.from_sequence + request.count - 1
    if last > session.next_outbound - 1:
        return RecoveryRejection.RECOVERY_OUT_OF_RANGE
    replay = session.reports[request.from_sequence - 1 : last]
    control = SequenceControl(
        session.session_id, session.version, FlowDirection.OUTBOUND, session.next_outbound
    )
    return (*replay, control)
