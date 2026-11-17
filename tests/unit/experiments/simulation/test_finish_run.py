"""finish_run turns the store snapshot into the finalised run snapshot."""

import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.simulation.finish_run import finish_run
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import MissionData
from rescue.mission.rules import register
from rescue.mobilisation.models import MobilisationPolicy


class FinishRunTests(unittest.TestCase):
    def test_returns_snapshot_whose_run_carries_the_summary(self) -> None:
        mission = register(
            MissionData(mission_id="M-1", station_name="S", people_count=2, created_at=0)
        )
        state = SimpleNamespace(
            missions=(mission,),
            market=B3Market(market_id="RUN-market"),
            command_index=(),
            message_index=(),
            delivery_index=(),
            decision_index=(),
            session_index=(),
        )
        handle = SimpleNamespace(store=SimpleNamespace(snapshot=lambda: state))
        scenario = SimpleNamespace(scenario_id="SCENARIO-1", revision=1)
        policy = MobilisationPolicy(
            policy_id="EARLIEST",
            revision=1,
            name="Earliest",
            selection_criteria="earliest_arrival",
        )
        snapshot = finish_run(
            handle,
            scenario,
            policy,
            "RUN",
            Decimal("0"),
            Decimal("10"),
            "horizon_reached",
        )
        self.assertEqual(snapshot.missions, (mission,))
        self.assertEqual(snapshot.run.status, "horizon_reached")
        self.assertEqual(snapshot.run.finished_at, Decimal("10"))
        self.assertEqual(snapshot.run.scenario_id, "SCENARIO-1")
        self.assertEqual(snapshot.run.result.unmet_demand, 2)
        self.assertFalse(snapshot.run.result.completed)


if __name__ == "__main__":
    unittest.main()
