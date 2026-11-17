"""Find a communication session in a run state.

What: returns the stored session with this id, or None when the run has none.
When called: by record_response, synchronise_inbound and get_session.
Why: every session command and the response session step look sessions up the same way.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.communication.models import CommunicationSession
from rescue.state import RunState


def find_session(state: RunState, session_id: str) -> CommunicationSession | None:
    """Find session.

    What: returns the communication session with this id from the session index, or None.
    When called: by get_session, recover_reports, synchronise_inbound, replace_session and resolve_session.
    Why: one lookup definition for every step that reads a session.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return next((item for item in state.session_index if item.session_id == session_id), None)
