"""End-to-end rescue and policy comparison demonstration."""

import unittest

from rescue.demo import render, run_demo
from rescue.mission.rules import progress


class RescueDemoTests(unittest.TestCase):
    def test_demand_ten_demo_completes_only_after_confirmed_seats_reach_demand(self):
        report = run_demo()

        mission = report.primary_run.missions[0]
        state = progress(mission)
        self.assertEqual(state.demand, 10)
        self.assertEqual(state.confirmed, 10)
        self.assertEqual(state.pending, 0)
        self.assertEqual(state.status, "complete")
        self.assertEqual(report.primary_run.run.result.confirmed_seats, 10)
        self.assertEqual(report.primary_run.run.result.unmet_demand, 0)
        self.assertEqual(
            {request.outcome for request in mission.requests},
            {"partially_accepted", "refused", "accepted"},
        )
        self.assertEqual(
            {request.ship_id for request in mission.requests},
            {"SHIP-EARLY", "SHIP-LARGE"},
        )
        self.assertGreaterEqual(len(mission.requests), 4)

    def test_two_policies_are_compared_for_all_three_scenario_types(self):
        report = run_demo()

        comparisons = {comparison.scenario_id: comparison.runs for comparison in report.comparisons}
        self.assertEqual(
            set(comparisons),
            {"SCENARIO-ORDINARY", "SCENARIO-PARTIAL-REFUSAL", "SCENARIO-DELAYED-LOSS"},
        )
        for runs in comparisons.values():
            self.assertEqual(len(runs), 2)
            self.assertEqual(
                {run.run.policy_id for run in runs},
                {"EARLIEST", "LARGEST"},
            )
        self.assertTrue(all(run.run.result.completed for run in comparisons["SCENARIO-ORDINARY"]))
        self.assertTrue(
            all(
                all(
                    request.outcome == "accepted"
                    for mission in run.missions
                    for request in mission.requests
                )
                for run in comparisons["SCENARIO-ORDINARY"]
            )
        )
        self.assertTrue(
            all(run.run.result.completed for run in comparisons["SCENARIO-PARTIAL-REFUSAL"])
        )
        self.assertTrue(
            all(
                {request.outcome for mission in run.missions for request in mission.requests}
                >= {"partially_accepted", "refused"}
                for run in comparisons["SCENARIO-PARTIAL-REFUSAL"]
            )
        )
        self.assertTrue(
            all(not run.run.result.completed for run in comparisons["SCENARIO-DELAYED-LOSS"])
        )
        for run in comparisons["SCENARIO-DELAYED-LOSS"]:
            self.assertEqual(
                run.market.availabilities[-1].availability_id,
                "AVAIL-EARLY-REDUCED",
            )
            self.assertTrue(
                any(
                    delivery.disposition == "lost"
                    for _, deliveries in run.message_index
                    for delivery in deliveries
                )
            )

    def test_rendered_output_reports_completion_and_comparison_count(self):
        output = render(run_demo())

        self.assertIn("confirmed=10", output)
        self.assertIn("pending=0", output)
        self.assertIn("status=complete", output)
        self.assertIn("comparisons=3 scenarios x 2 policies", output)

    def test_step_log_shows_partial_acceptance_refusal_and_the_follow_up_request(self):
        output = render(run_demo())

        self.assertIn("step log: mission MISSION-DEMO, demand 10", output)
        self.assertIn("partially_accepted", output)
        self.assertIn("refused", output)
        self.assertIn("request_created", output)
        self.assertGreaterEqual(output.count("  request "), 4)


if __name__ == "__main__":
    unittest.main()
