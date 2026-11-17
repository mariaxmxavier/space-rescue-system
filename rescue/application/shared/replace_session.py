"""Replace a communication session in a run state.

What: returns the state with the session replaced by id, or appended when it is new.
When called: by record_response, synchronise_inbound and recover_reports.
Why: the session index holds one value per id, so a new version replaces the old one.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.application.shared.find_session import find_session
from rescue.communication.models import CommunicationSession
from rescue.state import RunState


def replace_session(state: RunState, session: CommunicationSession) -> RunState:
    """Replace session.

    What: returns the state with the session replaced in the session index, or added when it is new.
    When called: by publish_delivery and synchronise_inbound.
    Why: one write path keeps the session index consistent after every session change.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    if find_session(state, session.session_id) is None:
        return replace(state, session_index=(*state.session_index, session))
    return replace(
        state,
        session_index=tuple(
            session if item.session_id == session.session_id else item
            for item in state.session_index
        ),
    )
