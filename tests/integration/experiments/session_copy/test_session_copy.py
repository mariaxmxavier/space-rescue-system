import unittest

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.experiments.models import RescueScenario, RunBaseline, ScriptedResponse
from rescue.experiments.simulation import simulate
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision
from rescue.mobilisation.models import MobilisationPolicy

SESSION_ID = "local:SHIP-1"


def _policy():
    return MobilisationPolicy("POLICY", 1, "POLICY", "earliest_arrival")


def _baseline(*, received_first):
    context = new_run("BASE", "BASE-CENTRAL")
    central = context.central
    central.register_mission(RegisterMission("MISSION-1", "Station", 2, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 4, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer("OFFER-1", "MISSION-1", "SHIP-1", ShipOfferRevision("REV-1", 1, 4, 5, True, 0))
    )
    request_ids = [
        central.create_request(
            CreateRequest(
                command_id=f"COMMAND-{number}",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=1,
                revision_id="REV-1",
                now=0,
            )
        ).value.request_id
        for number in (1, 2)
    ]
    if received_first:
        central.record_response(
            RecordResponse(
                message_id="MSG-1",
                delivery_id="DEL-1",
                attempt_number=1,
                request_id=request_ids[0],
                outcome="accepted",
                confirmed_seats=1,
                sent_at=1,
                received_at=2,
            )
        )
    state = context.store.snapshot()
    return RunBaseline(
        missions=state.missions,
        market=state.market,
        command_index=state.command_index,
        message_index=state.message_index,
        delivery_index=state.delivery_index,
        decision_index=state.decision_index,
        session_index=state.session_index,
    )


def _scenario(baseline, ordinal, name="SCENARIO"):
    rules = () if ordinal is None else (ScriptedResponse("SHIP-1", ordinal, "accepted"),)
    return RescueScenario(
        scenario_id=name,
        revision=1,
        name=name,
        baseline=baseline,
        response_rules=rules,
        availability_changes=(),
        time_horizon_seconds=8,
        seed=3,
        event_budget=100,
    )


def _session(snapshot):
    return next(item for item in snapshot.session_index if item.session_id == SESSION_ID)


class SessionCopyTests(unittest.TestCase):
    def test_copied_run_continues_baseline_session_counters_and_reports(self):
        """A run copied from a baseline with a session continues its counters and reports."""
        baseline = _baseline(received_first=True)
        source = baseline.session_index[0]

        snapshot = simulate(_scenario(baseline, 2), _policy(), "RUN-A", start_run=new_run)

        copied = _session(snapshot)
        self.assertEqual(copied.session_id, source.session_id)
        self.assertEqual(copied.version, source.version)
        self.assertEqual(copied.next_inbound, source.next_inbound + 1)
        self.assertEqual(copied.next_outbound, source.next_outbound + 1)
        self.assertEqual(copied.reports[: len(source.reports)], source.reports)
        self.assertEqual(
            [report.envelope.sequence for report in copied.reports],
            list(range(1, copied.next_outbound)),
        )
        self.assertEqual(len(snapshot.session_index), 1)

    def test_source_baseline_is_unchanged_after_copied_run_executes(self):
        """The source baseline and its session are unchanged after a copied run executes."""
        baseline = _baseline(received_first=True)
        session_before = baseline.session_index[0]
        counters_before = (session_before.next_inbound, session_before.next_outbound)
        reports_before = len(session_before.reports)

        simulate(_scenario(baseline, 2), _policy(), "RUN-A", start_run=new_run)

        self.assertEqual(baseline, _baseline(received_first=True))
        self.assertIs(baseline.session_index[0], session_before)
        self.assertEqual(
            (session_before.next_inbound, session_before.next_outbound), counters_before
        )
        self.assertEqual(len(session_before.reports), reports_before)

    def test_two_independent_runs_keep_separate_sessions(self):
        """Two runs from one baseline keep separate sessions and neither sees the other."""
        baseline = _baseline(received_first=True)
        source = baseline.session_index[0]

        advanced = simulate(
            _scenario(baseline, 2, "ADVANCE"), _policy(), "RUN-A", start_run=new_run
        )
        idle = simulate(_scenario(baseline, None, "IDLE"), _policy(), "RUN-B", start_run=new_run)

        self.assertEqual(_session(advanced).next_inbound, source.next_inbound + 1)
        self.assertEqual(_session(idle), source)
        self.assertEqual(len(_session(advanced).reports), len(source.reports) + 1)
        self.assertEqual(len(_session(idle).reports), len(source.reports))
        self.assertEqual(baseline.session_index, (source,))

    def test_baseline_without_session_index_runs_and_default_session_starts_at_one(self):
        """A baseline without a session index still runs and its default session starts at 1."""
        baseline = _baseline(received_first=False)
        self.assertEqual(baseline.session_index, ())

        snapshot = simulate(_scenario(baseline, 1), _policy(), "RUN-A", start_run=new_run)

        created = _session(snapshot)
        self.assertEqual(created.version, 1)
        self.assertEqual(created.next_inbound, 2)
        self.assertEqual(created.next_outbound, 2)
        self.assertEqual([report.envelope.sequence for report in created.reports], [1])
        self.assertEqual(baseline.session_index, ())


if __name__ == "__main__":
    unittest.main()
