"""Tests that RescueCentral hands each call to its service.

What: compares the facade result with the direct service call on the same state.
When called: by pytest with the application unit tests.
Why: the facade holds no logic, so its only duty is to pass the right ports to the right service.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import dataclasses
import unittest

from rescue.adapters.memory import ZeroClock
from rescue.application.central import RescueCentral
from rescue.application.contracts import ComparePolicies, RegisterMission
from rescue.application.services.comparison.compare_policies import compare_policies
from rescue.application.services.missions.register_mission import register_mission
from tests.unit.application.services.fakes import FakeIds, FakeSimulator, FakeStore, empty_state


@dataclasses.dataclass(frozen=True)
class StubScenario:
    scenario_id: str
    revision: int


@dataclasses.dataclass(frozen=True)
class StubPolicy:
    policy_id: str
    revision: int


def central(state, snapshots=()):
    return RescueCentral(
        application_run_id="run-1",
        central_id="central-1",
        store=FakeStore(state),
        clock=ZeroClock(),
        id_source=FakeIds(),
        simulator=FakeSimulator(snapshots),
    )


class CentralDelegationTest(unittest.TestCase):
    def test_register_mission_returns_the_service_result(self):
        command = RegisterMission("mission-1", "Station", 5, 0)
        expected = register_mission(command, store=FakeStore(empty_state()))

        self.assertEqual(expected, central(empty_state()).register_mission(command))

    def test_compare_returns_the_service_result_using_the_simulator(self):
        state = dataclasses.replace(
            empty_state(),
            scenarios=(StubScenario("scenario-1", 1),),
            policies=(StubPolicy("policy-a", 1),),
        )
        command = ComparePolicies("scenario-1", 1, (("policy-a", 1),))
        expected = compare_policies(
            command,
            store=FakeStore(state),
            id_source=FakeIds(),
            simulator=FakeSimulator(["snap-1"]),
        )

        self.assertEqual(expected, central(state, ["snap-1"]).compare(command))
