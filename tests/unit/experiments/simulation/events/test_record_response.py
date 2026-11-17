"""record_response records the response and reschedules mobilise on a first applied attempt."""

import itertools
import random
import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.simulation._payload import _ResponsePayload
from rescue.experiments.simulation.events.record_response import record_response
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline, TimelineEvent


def session_with(status):
    calls = []

    def record(command):
        calls.append(command)
        return SimpleNamespace(status=status)

    session = SimulationSession(
        handle=SimpleNamespace(
            store=None,
            id_source=SimpleNamespace(next_id=lambda kind: f"{kind}-1"),
            central=SimpleNamespace(record_response=record),
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


def response_event(attempt_number=1, received_at=Decimal("4")):
    payload = _ResponsePayload(
        message_id="MSG-1",
        mission_id="M-1",
        request_id="R-1",
        outcome="accepted",
        confirmed_seats=2,
        attempt_number=attempt_number,
        sent_at=Decimal("3"),
        received_at=received_at,
        communication_rtt_seconds=Decimal("1"),
    )
    return TimelineEvent(
        instant=Decimal("4"), kind="response", scenario_sequence=9, payload=payload
    )


class RecordResponseTests(unittest.TestCase):
    def test_first_applied_attempt_records_and_schedules_mobilise(self) -> None:
        session, calls = session_with("applied")
        record_response(session, response_event(), Decimal("4"))
        self.assertEqual(calls[0].delivery_id, "delivery-1")
        self.assertEqual(calls[0].message_id, "MSG-1")
        self.assertEqual(calls[0].confirmed_seats, 2)
        scheduled = session.timeline.pop_next()
        self.assertEqual(
            (scheduled.instant, scheduled.kind, scheduled.payload),
            (Decimal("4"), "mobilise", "M-1"),
        )

    def test_duplicate_lost_or_unapplied_responses_schedule_nothing(self) -> None:
        cases = (
            ("applied", response_event(attempt_number=2)),
            ("applied", response_event(received_at=None)),
            ("replayed", response_event()),
        )
        for status, event in cases:
            session, _ = session_with(status)
            record_response(session, event, Decimal("4"))
            self.assertIsNone(session.timeline.pop_next())


if __name__ == "__main__":
    unittest.main()
