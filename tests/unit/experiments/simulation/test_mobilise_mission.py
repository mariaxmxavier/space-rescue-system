"""mobilise_mission asks the central to mobilise a mission and schedules each new request."""

import itertools
import random
import sys
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from rescue.experiments.simulation.mobilise_mission import mobilise_mission
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import DomainValidationError

MODULE = sys.modules["rescue.experiments.simulation.mobilise_mission"]
MISSION = SimpleNamespace(mission_id="m1")


def evaluation(ship_id):
    return SimpleNamespace(
        ship_id=ship_id, proposed_seats=2, revision=SimpleNamespace(revision_id=f"rev-{ship_id}")
    )


def new_session(selection, created=("applied", "applied")):
    created_results = iter(created)
    log = SimpleNamespace(mobilise=[], create=[], ids=[])
    central = SimpleNamespace(
        mobilise=lambda command: log.mobilise.append(command) or selection,
        create_request=lambda command: (
            log.create.append(command)
            or SimpleNamespace(status=next(created_results), value=f"req-{len(log.create)}")
        ),
    )
    handle = SimpleNamespace(
        store=SimpleNamespace(snapshot=lambda: SimpleNamespace(missions=(MISSION,))),
        id_source=SimpleNamespace(
            next_id=lambda kind: log.ids.append(kind) or f"{kind}-{len(log.ids)}"
        ),
        central=central,
    )
    session = SimulationSession(
        handle=handle,
        policy=MobilisationPolicy(
            policy_id="EARLIEST", revision=1, name="Earliest", selection_criteria="earliest_arrival"
        ),
        timeline=Timeline(horizon=10, event_budget=5),
        rng=random.Random(1),
        sequence=itertools.count(1),
        response_rules={},
        profiles={},
        ship_ordinals={},
    )
    return session, log


def applied(*ships):
    return SimpleNamespace(
        status="applied",
        value=SimpleNamespace(decision_id="d1", selected=tuple(evaluation(s) for s in ships)),
    )


def needed(count):
    return patch.object(
        MODULE, "progress", lambda mission: SimpleNamespace(additional_needed=count)
    )


class MobiliseMissionTests(unittest.TestCase):
    def test_returns_early_when_nothing_is_needed(self) -> None:
        session, log = new_session(applied())
        with needed(0):
            mobilise_mission(session, "m1", Decimal("1"))
        self.assertEqual(log.mobilise, [])

    def test_raises_when_selection_is_not_applied(self) -> None:
        session, _ = new_session(SimpleNamespace(status="rejected", reason="no ships"))
        with (
            needed(2),
            self.assertRaisesRegex(DomainValidationError, "scenario mobilisation failed: no ships"),
        ):
            mobilise_mission(session, "m1", Decimal("1"))

    def test_creates_one_request_per_evaluation_and_schedules_applied_ones(self) -> None:
        session, log = new_session(applied("s1", "s2"), created=("applied", "rejected"))
        with needed(2), patch.object(MODULE, "schedule_request_events") as schedule:
            mobilise_mission(session, "m1", Decimal("1"))
        self.assertEqual([c.ship_id for c in log.create], ["s1", "s2"])
        self.assertEqual([c.command_id for c in log.create], ["command-1", "command-2"])
        self.assertEqual(log.create[0].decision_id, "d1")
        schedule.assert_called_once_with(session, "m1", "req-1")


if __name__ == "__main__":
    unittest.main()
