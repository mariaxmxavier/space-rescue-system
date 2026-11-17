"""schedule_initial_events seeds the timeline from the baseline and the scenario."""

import itertools
import random
import unittest
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.models import ScriptedResponse
from rescue.experiments.simulation.schedule_initial_events import schedule_initial_events
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mission.models import RequestOutcome


@dataclass(frozen=True)
class Availability:
    recorded_at: Decimal


def make_request(request_id, ship_id, outcome, deadline):
    return SimpleNamespace(
        request_id=request_id,
        ship_id=ship_id,
        outcome=outcome,
        response_deadline=deadline,
        requested_seats=2,
        submitted_at=Decimal("1"),
    )


def drain(timeline):
    events = []
    while (event := timeline.pop_next()) is not None:
        events.append(event)
    return events


class ScheduleInitialEventsTests(unittest.TestCase):
    def test_orders_mobilise_availability_then_pending_requests(self) -> None:
        rule = ScriptedResponse(ship_id="s1", request_ordinal=2, outcome=RequestOutcome.ACCEPTED)
        requests = (
            make_request("done", "s1", RequestOutcome.ACCEPTED, Decimal("50")),
            make_request("late", "s1", RequestOutcome.PENDING, Decimal("2")),
            make_request("open", "s2", RequestOutcome.PENDING, None),
        )
        missions = (
            SimpleNamespace(mission_id="m1", requests=requests),
            SimpleNamespace(mission_id="m2", requests=()),
        )
        calls = []
        handle = SimpleNamespace(
            id_source=SimpleNamespace(next_id=lambda kind: calls.append(kind) or "msg-1")
        )
        session = SimulationSession(
            handle=handle,
            policy=None,
            timeline=Timeline(horizon=100, event_budget=20),
            rng=random.Random(1),
            sequence=itertools.count(1),
            response_rules={("s1", 2): rule},
            profiles={},
            ship_ordinals={},
        )
        scenario = SimpleNamespace(availability_changes=(Availability(Decimal("4")),))
        schedule_initial_events(session, SimpleNamespace(missions=missions), scenario, Decimal("3"))
        events = drain(session.timeline)
        summary = [(e.scenario_sequence, e.kind, e.instant) for e in events]
        self.assertEqual(
            sorted(summary),
            [
                (1, "mobilise", Decimal("3")),
                (2, "mobilise", Decimal("3")),
                (3, "availability", Decimal("7")),
                (4, "expire", Decimal("3")),
                (5, "response", Decimal("1")),
            ],
        )
        self.assertEqual(calls, ["message"])
        self.assertEqual(session.ship_ordinals, {"s1": 2, "s2": 1})
        availability = next(e for e in events if e.kind == "availability")
        self.assertEqual(availability.payload.recorded_at, Decimal("7"))


if __name__ == "__main__":
    unittest.main()
