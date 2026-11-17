"""schedule_response queues one or two response events from a rule and a profile."""

import itertools
import random
import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.models import CommunicationProfile, ScriptedResponse
from rescue.experiments.simulation.schedule_response import schedule_response
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mission.models import RequestOutcome


def new_session() -> SimulationSession:
    return SimulationSession(
        handle=SimpleNamespace(),
        policy=None,
        timeline=Timeline(horizon=100, event_budget=10),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules={},
        profiles={},
        ship_ordinals={},
    )


def drain(timeline: Timeline) -> list:
    events = []
    while (event := timeline.pop_next()) is not None:
        events.append(event)
    return events


RULE = ScriptedResponse(ship_id="s1", request_ordinal=1, outcome=RequestOutcome.ACCEPTED)
MISSION = SimpleNamespace(mission_id="m1")
REQUEST = SimpleNamespace(request_id="r1", requested_seats=3, submitted_at=Decimal("5"))


def profile(**rules) -> CommunicationProfile:
    return CommunicationProfile(
        profile_id="p1",
        ship_id="s1",
        outbound_delay_seconds=1,
        decision_delay_seconds=2,
        return_delay_seconds=3,
        **rules,
    )


def schedule(session, prof, ordinal=1):
    schedule_response(session, RULE, MISSION, REQUEST, ordinal, prof, "msg-1")
    return drain(session.timeline)


class ScheduleResponseTests(unittest.TestCase):
    def test_no_profile_has_zero_delays(self) -> None:
        (event,) = schedule(new_session(), None)
        self.assertEqual(event.kind, "response")
        self.assertEqual(event.instant, Decimal("5"))
        self.assertEqual(event.scenario_sequence, 1)
        self.assertEqual(event.priority, 1)
        payload = event.payload
        self.assertEqual(payload.received_at, Decimal("5"))
        self.assertEqual(payload.communication_rtt_seconds, Decimal("0"))
        self.assertEqual((payload.outcome, payload.confirmed_seats), ("accepted", 3))
        self.assertEqual(
            (payload.message_id, payload.mission_id, payload.request_id), ("msg-1", "m1", "r1")
        )
        self.assertEqual(payload.attempt_number, 1)

    def test_profile_delays_shift_times(self) -> None:
        (event,) = schedule(new_session(), profile())
        self.assertEqual(event.instant, Decimal("11"))
        self.assertEqual(event.payload.sent_at, Decimal("8"))
        self.assertEqual(event.payload.communication_rtt_seconds, Decimal("4"))

    def test_lost_response_has_no_receipt(self) -> None:
        (event,) = schedule(new_session(), profile(loss_rule=(1,)))
        self.assertIsNone(event.payload.received_at)
        self.assertIsNone(event.payload.communication_rtt_seconds)

    def test_duplicated_response_schedules_two_attempts(self) -> None:
        events = schedule(new_session(), profile(duplication_rule=(1,)))
        self.assertEqual([e.payload.attempt_number for e in events], [1, 2])
        self.assertEqual([e.scenario_sequence for e in events], [1, 2])

    def test_reordered_response_has_priority_two(self) -> None:
        (event,) = schedule(new_session(), profile(reordering_rule=(1,)))
        self.assertEqual(event.priority, 2)


if __name__ == "__main__":
    unittest.main()
