"""SimulationSession holds one run's mutable state in an immutable container."""

import itertools
import random
import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mobilisation.models import MobilisationPolicy


def new_session() -> SimulationSession:
    return SimulationSession(
        handle=SimpleNamespace(store=None, id_source=None, central=None),
        policy=MobilisationPolicy(
            policy_id="EARLIEST",
            revision=1,
            name="Earliest arrival",
            selection_criteria="earliest_arrival",
        ),
        timeline=Timeline(horizon=10, event_budget=5),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules={},
        profiles={},
        ship_ordinals={},
    )


class SimulationSessionTests(unittest.TestCase):
    def test_session_is_frozen(self) -> None:
        session = new_session()
        with self.assertRaises(FrozenInstanceError):
            session.policy = None

    def test_sequence_yields_one_two_three(self) -> None:
        session = new_session()
        self.assertEqual([next(session.sequence) for _ in range(3)], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
