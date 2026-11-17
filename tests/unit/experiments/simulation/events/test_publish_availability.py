"""publish_availability sends the availability to the central and rejects failures."""

import itertools
import random
import unittest
from decimal import Decimal
from types import SimpleNamespace

from rescue.experiments.simulation.events.publish_availability import publish_availability
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline, TimelineEvent
from rescue.values import DomainValidationError


def session_with(result):
    calls = []

    def publish(command):
        calls.append(command)
        return result

    central = SimpleNamespace(publish_availability=publish)
    session = SimulationSession(
        handle=SimpleNamespace(store=None, id_source=None, central=central),
        policy=None,
        timeline=Timeline(horizon=10, event_budget=5),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules={},
        profiles={},
        ship_ordinals={},
    )
    return session, calls


def availability_event():
    return TimelineEvent(
        instant=Decimal("1"), kind="availability", scenario_sequence=1, payload="AVAILABILITY"
    )


class PublishAvailabilityTests(unittest.TestCase):
    def test_applied_and_replayed_publications_pass(self) -> None:
        for status in ("applied", "replayed"):
            session, calls = session_with(SimpleNamespace(status=status, reason=None))
            publish_availability(session, availability_event(), Decimal("1"))
            self.assertEqual(calls[0].availability, "AVAILABILITY")

    def test_failed_publication_raises_the_legacy_message(self) -> None:
        session, _ = session_with(SimpleNamespace(status="rejected", reason="bad"))
        with self.assertRaisesRegex(
            DomainValidationError, "^scenario availability change failed: bad$"
        ):
            publish_availability(session, availability_event(), Decimal("1"))


if __name__ == "__main__":
    unittest.main()
