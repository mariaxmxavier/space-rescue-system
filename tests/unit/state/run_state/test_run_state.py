"""Run state validation tests."""

import unittest

from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.state import RunState
from rescue.values import DomainValidationError

INDEX_FIELDS = (
    "command_index",
    "message_index",
    "delivery_index",
    "decision_index",
    "policies",
    "scenarios",
    "completed_runs",
)


def mission(mission_id="MISSION-1"):
    """Build a mission for placing in a run state.

    What: a small mission with the given id.
    When called: by the run state tests that need a valid mission value.
    Why: run state validation depends only on mission identity and type.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return Mission(mission_id, "Station One", 6, 0)


def run_state(**overrides):
    """Build a run state with the required fields, adding any overrides.

    What: a run state for one application run with a B3 market and no other state.
    When called: by the run state tests, with one field as the override under test.
    Why: each test names only the field it checks.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    fields = {
        "application_run_id": "RUN-1",
        "central_id": "CENTRAL-1",
        "market": B3Market(market_id="MARKET-RUN-1"),
    }
    return RunState(**(fields | overrides))


class RunStateTests(unittest.TestCase):
    """Run state rejects invalid composition and finds missions by id.

    What: the validation and the mission lookup of the run state.
    When called: whenever a run state is built or replaced by a transaction.
    Why: a run's state is published whole, so an invalid or mutable value must never enter it.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_rejects_a_market_that_is_not_a_b3_market(self):
        with self.assertRaises(DomainValidationError):
            run_state(market="MARKET-RUN-1")

    def test_rejects_a_mission_that_is_not_a_mission(self):
        with self.assertRaises(DomainValidationError):
            run_state(missions=("MISSION-1",))

    def test_rejects_duplicate_mission_ids(self):
        with self.assertRaisesRegex(
            DomainValidationError, "mission IDs must be unique within a run"
        ):
            run_state(missions=(mission("MISSION-1"), mission("MISSION-1")))

    def test_rejects_a_mutable_value_in_any_index(self):
        for field_name in (*INDEX_FIELDS, "session_index"):
            with self.subTest(field_name=field_name), self.assertRaises(DomainValidationError):
                run_state(**{field_name: ([],)})

    def test_rejects_a_mission_that_hides_a_mutable_value(self):
        tampered = mission()
        object.__setattr__(tampered, "station_name", [])

        with self.assertRaisesRegex(DomainValidationError, "deeply immutable"):
            run_state(missions=(tampered,))

    def test_mission_returns_the_mission_or_none(self):
        first = mission("MISSION-1")
        state = run_state(missions=(first, mission("MISSION-2")))

        self.assertIs(state.mission("MISSION-1"), first)
        self.assertIsNone(state.mission("MISSION-9"))


if __name__ == "__main__":
    unittest.main()
