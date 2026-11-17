"""Tests of the compare_policies service.

What: proves policies are simulated in order on one scenario and bad input is rejected.
When called: by pytest with the rest of the application unit tests; covers RescueCentral.compare.
Why: comparison must read one snapshot, simulate each policy once, and reject bad keys with invalid_input.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import dataclasses
import unittest

from rescue.application.contracts import ComparePolicies
from rescue.application.services.comparison.compare_policies import compare_policies
from tests.unit.application.services.fakes import FakeIds, FakeSimulator, FakeStore, empty_state


@dataclasses.dataclass(frozen=True)
class StubScenario:
    scenario_id: str
    revision: int


@dataclasses.dataclass(frozen=True)
class StubPolicy:
    policy_id: str
    revision: int


SCENARIO = StubScenario("scenario-1", 1)
POLICY_A = StubPolicy("policy-a", 1)
POLICY_B = StubPolicy("policy-b", 2)


def run(policy_keys, scenario_revision=1, snapshots=("snap-1", "snap-2")):
    state = dataclasses.replace(empty_state(), scenarios=(SCENARIO,), policies=(POLICY_A, POLICY_B))
    simulator = FakeSimulator(snapshots)
    command = ComparePolicies("scenario-1", scenario_revision, policy_keys)
    result = compare_policies(
        command, store=FakeStore(state), id_source=FakeIds(), simulator=simulator
    )
    return result, simulator


class ComparePoliciesTests(unittest.TestCase):
    def test_simulates_each_policy_in_order_with_a_fresh_simulation_id(self):
        result, simulator = run((("policy-b", 2), ("policy-a", 1)))

        self.assertEqual("applied", result.status)
        self.assertEqual(("snap-1", "snap-2"), result.value)
        self.assertEqual(
            [
                (SCENARIO, POLICY_B, "simulation-1"),
                (SCENARIO, POLICY_A, "simulation-2"),
            ],
            simulator.calls,
        )

    def assert_rejected(self, result, simulator):
        self.assertEqual("rejected", result.status)
        self.assertEqual("invalid_input", result.reason)
        self.assertEqual([], simulator.calls)

    def test_rejects_an_empty_policy_list(self):
        self.assert_rejected(*run(()))

    def test_rejects_a_duplicate_policy_key(self):
        self.assert_rejected(*run((("policy-a", 1), ("policy-a", 1))))

    def test_rejects_a_malformed_policy_key(self):
        self.assert_rejected(*run((("policy-a",),)))

    def test_rejects_an_unknown_scenario_revision(self):
        self.assert_rejected(*run((("policy-a", 1),), scenario_revision=9))

    def test_rejects_an_unknown_policy_revision(self):
        self.assert_rejected(*run((("policy-a", 9),)))
