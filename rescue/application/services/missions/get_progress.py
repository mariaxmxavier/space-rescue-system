"""Read the seat progress of a mission.

What: returns the progress of the mission, or rejects an unknown mission or a bad instant.
When called: by RescueCentral.get_progress, which hands it the mission id, the instant and the store.
Why: callers see how many seats still need a ship without touching the run state.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.mission import rules as mission_rules
from rescue.mission.models import MissionProgress
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_instant


def get_progress(mission_id: str, now, *, store: TransactionStore) -> Result[MissionProgress]:
    """Return the seat progress of a mission at an instant.

    What: Validate the instant, look up the mission and answer with its progress, leaving the state unchanged.
    When called: RescueCentral.get_progress in rescue/application/central.py.
    Why: Callers see how many seats still need a ship without touching the run state. A read must not alter the run; a bad instant or unknown mission is rejected with a reason.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of get_progress.

        What: applies the get_progress rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by get_progress, which runs it once per call.
        Why: A read must not alter the run; a bad instant or unknown mission is rejected with a reason.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            normalize_instant(now)
            mission = find_mission(state, mission_id)
            if mission is None:
                return state, make_result("rejected", reason="unknown_mission")
            return state, make_result("applied", mission_rules.progress(mission))
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
