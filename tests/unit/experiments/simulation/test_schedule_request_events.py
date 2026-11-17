"""schedule_request_events queues the expiry and the scripted response of a new request."""

import itertools
import random
import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.models import ScriptedResponse
from rescue.experiments.simulation.schedule_request_events import schedule_request_events
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mission.models import RequestOutcome

MISSION = SimpleNamespace(mission_id="m1")


def new_session(rules=None):
    calls = []
    handle = SimpleNamespace(
        store=SimpleNamespace(snapshot=lambda: SimpleNamespace(missions=(MISSION,))),
        id_source=SimpleNamespace(next_id=lambda kind: calls.append(kind) or f"{kind}-1"),
    )
    session = SimulationSession(
        handle=handle,
        policy=None,
        timeline=Timeline(horizon=100, event_budget=10),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules=rules or {},
        profiles={},
        ship_ordinals={},
    )
    return session, calls


def request(deadline=Decimal("9")):
    return SimpleNamespace(
        request_id="r1",
        ship_id="s1",
        requested_seats=2,
        submitted_at=Decimal("1"),
        response_deadline=deadline,
    )


def drain(timeline):
    events = []
    while (event := timeline.pop_next()) is not None:
        events.append(event)
    return events


class ScheduleRequestEventsTests(unittest.TestCase):
    def test_deadline_schedules_expire_and_no_rule_means_no_message_id(self) -> None:
        session, calls = new_session()
        schedule_request_events(session, "m1", request())
        (event,) = drain(session.timeline)
        self.assertEqual(
            (event.kind, event.instant, event.payload), ("expire", Decimal("9"), ("m1", "r1"))
        )
        self.assertEqual(session.ship_ordinals, {"s1": 1})
        self.assertEqual(calls, [])

    def test_no_deadline_schedules_nothing_but_still_counts_the_ordinal(self) -> None:
        session, _ = new_session()
        schedule_request_events(session, "m1", request(deadline=None))
        self.assertEqual(drain(session.timeline), [])
        self.assertEqual(session.ship_ordinals, {"s1": 1})

    def test_matching_rule_schedules_response_after_expire(self) -> None:
        rule = ScriptedResponse(ship_id="s1", request_ordinal=2, outcome=RequestOutcome.ACCEPTED)
        session, calls = new_session({("s1", 2): rule})
        session.ship_ordinals["s1"] = 1
        schedule_request_events(session, "m1", request())
        events = drain(session.timeline)
        self.assertEqual(session.ship_ordinals, {"s1": 2})
        self.assertEqual(calls, ["message"])
        self.assertEqual([e.kind for e in events], ["response", "expire"])
        self.assertEqual([e.scenario_sequence for e in events], [2, 1])
        self.assertEqual(events[0].payload.message_id, "message-1")


if __name__ == "__main__":
    unittest.main()
