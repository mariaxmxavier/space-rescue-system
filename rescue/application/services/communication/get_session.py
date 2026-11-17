"""Return one session for diagnostics: version, both counters, gaps and reports.

What: looks the session up by id and returns it unchanged.
When called: by RescueCentral.get_session, for tests and operators inspecting a ship's sequenced exchange.
Why: an absent session is a named rejection, so a typo is not mistaken for an empty one.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_session import find_session
from rescue.application.shared.make_result import make_result
from rescue.communication.models import CommunicationSession
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def get_session(session_id: str, *, store: TransactionStore) -> Result[CommunicationSession]:
    """Return one communication session, or reject an unknown session id.

    What: finds the session by normalised id and returns it unchanged; absence is rejected as unknown_session.
    When called: by RescueCentral.get_session in rescue/application/central.py.
    Why: an absent session is a named rejection, so a mistyped id is not mistaken for an empty session.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            session = find_session(state, normalize_id(session_id))
            if session is None:
                return state, make_result("rejected", reason="unknown_session")
            return state, make_result("applied", session)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
