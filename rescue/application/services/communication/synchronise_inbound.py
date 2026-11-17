"""Move a session's expected inbound number forward to the one the ship will send next.

What: builds the inbound SequenceControl, applies the synchronise_inbound rule and publishes the
  session with any NotApplied gap; a refusal publishes nothing.
When called: by RescueCentral.synchronise_inbound, when a ship skips inbound numbers and tells central where it resumes.
Why: the skipped range becomes a visible gap without consuming a business number.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result, SynchroniseInbound
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_session import find_session
from rescue.application.shared.make_result import make_result
from rescue.application.shared.replace_session import replace_session
from rescue.communication import rules as communication_rules
from rescue.communication.models import (
    CommunicationSession,
    FlowDirection,
    RecoveryRejection,
    SequenceControl,
)
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def synchronise_inbound(
    command: SynchroniseInbound, *, store: TransactionStore
) -> Result[CommunicationSession]:
    """Move a session's expected inbound number to the one the ship sends next.

    What: builds an inbound SequenceControl, applies the synchronise_inbound rule and publishes the advanced session; a rejection publishes nothing.
    When called: by RescueCentral.synchronise_inbound in rescue/application/central.py.
    Why: the skipped inbound range becomes a visible gap without consuming a business number.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            session = find_session(state, normalize_id(command.session_id))
            if session is None:
                return state, make_result("rejected", reason="unknown_session")
            synchronised = communication_rules.synchronise_inbound(
                session,
                SequenceControl(
                    command.session_id,
                    command.version,
                    FlowDirection.INBOUND,
                    command.next_sequence,
                ),
            )
            if isinstance(synchronised, RecoveryRejection):
                return state, make_result("rejected", reason=synchronised.value)
            advanced, _gap = synchronised
            return replace_session(state, advanced), make_result("applied", advanced)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
