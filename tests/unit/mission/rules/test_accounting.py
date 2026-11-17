"""Seat accounting rejects a mission whose pending seats exceed its demand.

What: calls account() directly on missions that hold too many pending seats, and on a consistent one.
When called: every transition calls account() on its result; the guard is unreachable through the
public rules because each transition keeps the invariant, so it is tested at the helper.
Why: C + P <= D must hold even if a Mission is built inconsistently by a caller.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

import unittest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.mission.rules._accounting import account
from rescue.values import DomainValidationError


def _pending_request(request_id: str, requested: int) -> SeatRequest:
    return SeatRequest(
        request_id=request_id,
        command_id=f"command-{request_id}",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=requested,
        confirmed_seats=0,
        outcome=RequestOutcome.PENDING,
        submitted_at=1,
    )


def _mission(people_count: int, requests: tuple[SeatRequest, ...]) -> Mission:
    return Mission(
        mission_id="mission-1",
        station_name="Station",
        people_count=people_count,
        created_at=0,
        requests=requests,
    )


class AccountingGuardTests(unittest.TestCase):
    def test_pending_seats_above_demand_are_rejected(self):
        mission = _mission(3, (_pending_request("r1", 2), _pending_request("r2", 2)))

        with self.assertRaisesRegex(DomainValidationError, "seat accounting invariant violated"):
            account(mission)

    def test_consistent_mission_reports_confirmed_and_pending_seats(self):
        mission = _mission(3, (_pending_request("r1", 2),))

        self.assertEqual(account(mission), (0, 2))


if __name__ == "__main__":
    unittest.main()
