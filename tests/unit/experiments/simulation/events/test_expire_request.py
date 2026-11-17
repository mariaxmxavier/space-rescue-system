"""expire_request expires the request and reschedules mobilise at now when it applied."""

import itertools
import random
import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.simulation.events.expire_request import expire_request
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline, TimelineEvent


def session_with(status):
    calls = []

    def expire(command):
        calls.append(command)
        return SimpleNamespace(status=status)

    session = SimulationSession(
        handle=SimpleNamespace(
            store=None, id_source=None, central=SimpleNamespace(expire_request=expire)
        ),
        policy=None,
        timeline=Timeline(horizon=10, event_budget=5),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules={},
        profiles={},
        ship_ordinals={},
    )
    return session, calls


def expire_event():
    return TimelineEvent(
        instant=Decimal("3"), kind="expire", scenario_sequence=9, payload=("M-1", "R-1")
    )


class ExpireRequestTests(unittest.TestCase):
    def test_applied_expiry_schedules_mobilise_at_now(self) -> None:
        session, calls = session_with("applied")
        expire_request(session, expire_event(), Decimal("3"))
        self.assertEqual((calls[0].mission_id, calls[0].request_id), ("M-1", "R-1"))
        self.assertEqual(calls[0].now, Decimal("3"))
        scheduled = session.timeline.pop_next()
        self.assertEqual(
            (scheduled.instant, scheduled.kind, scheduled.scenario_sequence, scheduled.payload),
            (Decimal("3"), "mobilise", 1, "M-1"),
        )

    def test_not_applied_expiry_schedules_nothing(self) -> None:
        session, _ = session_with("rejected")
        expire_request(session, expire_event(), Decimal("3"))
        self.assertIsNone(session.timeline.pop_next())


if __name__ == "__main__":
    unittest.main()
