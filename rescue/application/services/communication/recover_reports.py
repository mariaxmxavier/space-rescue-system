"""Replay a session's retained decision reports, then the control for the live stream.

What: looks up the session and asks the recover_reports rule for the requested range; a
  RecoveryRejection becomes the rejected result with the same-named reason.
When called: by RescueCentral.recover_reports, when a ship has missed decision reports and asks for them again.
Why: recovery only reads retained reports, so the run state is returned unchanged and a replayed
  report keeps its original id, number and content.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import RecoverReports, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_session import find_session
from rescue.application.shared.make_result import make_result
from rescue.communication import rules as communication_rules
from rescue.communication.models import (
    DecisionReport,
    RecoveryRejection,
    RecoveryRequest,
    SequenceControl,
)
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def recover_reports(
    command: RecoverReports, *, store: TransactionStore
) -> Result[tuple[DecisionReport | SequenceControl, ...]]:
    """Replay a session's retained reports for the requested range.

    What: finds the session, asks the recover_reports rule for the range (a from_sequence below one is forced to a recovery-out-of-range rejection) and returns the replay or a rejection with the rejection's reason.
    When called: by RescueCentral.recover_reports in rescue/application/central.py.
    Why: recovery only reads retained reports, so the run state is returned unchanged and replayed reports keep their id, number and content.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            session = find_session(state, normalize_id(command.session_id))
            if session is None:
                return state, make_result("rejected", reason="unknown_session")
            below_one = type(command.from_sequence) is int and command.from_sequence < 1
            replay = communication_rules.recover_reports(
                session,
                RecoveryRequest(
                    command.session_id,
                    command.version,
                    1 if below_one else command.from_sequence,
                    command.count,
                ),
            )
            if below_one and not isinstance(replay, RecoveryRejection):
                replay = RecoveryRejection.RECOVERY_OUT_OF_RANGE
            if isinstance(replay, RecoveryRejection):
                return state, make_result("rejected", reason=replay.value)
            return state, make_result("applied", replay)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
