"""Register a rescue mission.

What: builds a Mission from the command and adds it to the run, or rejects it.
When called: by RescueCentral.register_mission, which hands it the command and the store.
Why: a mission must exist before ships can quote or be mobilised for it.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import RegisterMission, Result
from rescue.application.contracts.snapshots import MissionSnapshot
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.mission import rules as mission_rules
from rescue.mission.models import MissionData
from rescue.state import RunState
from rescue.values import DomainValidationError


def register_mission(
    command: RegisterMission, *, store: TransactionStore
) -> Result[MissionSnapshot]:
    """Build a Mission from the command and add it to the run.

    What: Build the mission through the mission rules, reject a taken mission id as identity_conflict, otherwise append it to the state.
    When called: RescueCentral.register_mission in rescue/application/central.py.
    Why: A mission must exist before ships can quote or be mobilised for it. The identity check keeps a mission id unique within a run.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of register_mission.

        What: applies the register_mission rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by register_mission, which runs it once per call.
        Why: The identity check keeps a mission id unique within a run.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            mission = mission_rules.register(
                MissionData(
                    command.mission_id,
                    command.station_name,
                    command.people_count,
                    command.created_at,
                )
            )
            if find_mission(state, mission.mission_id) is not None:
                return state, make_result("rejected", reason="identity_conflict")
            return replace(state, missions=(*state.missions, mission)), make_result(
                "applied", mission
            )
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
