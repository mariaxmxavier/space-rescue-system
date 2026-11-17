"""Read the request history of a mission.

What: returns the history entries of the mission, or rejects an unknown mission.
When called: by RescueCentral.get_history, which hands it the mission id and the store.
Why: callers audit what happened to a mission without touching the run state.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.mission.models import RequestHistoryEntry
from rescue.state import RunState
from rescue.values import DomainValidationError


def get_history(
    mission_id: str, *, store: TransactionStore
) -> Result[tuple[RequestHistoryEntry, ...]]:
    """Return the history entries of a mission, or reject an unknown mission.

    What: Look up the mission in the state and answer with its history, leaving the state unchanged.
    When called: RescueCentral.get_history in rescue/application/central.py.
    Why: Callers audit a mission without touching the run state. A read must not alter the run, so the step returns the state it received.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of get_history.

        What: applies the get_history rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by get_history, which runs it once per call.
        Why: A read must not alter the run, so the step returns the state it received.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            mission = find_mission(state, mission_id)
            if mission is None:
                return state, make_result("rejected", reason="unknown_mission")
            return state, make_result("applied", mission.history)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
