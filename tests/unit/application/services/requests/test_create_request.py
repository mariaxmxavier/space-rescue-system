"""create_request service tests."""

import unittest

from rescue.application.contracts import CreateRequest
from rescue.application.services.requests.create_request import create_request
from rescue.mission.models import RequestOutcome
from tests.unit.application.services.fakes import FakeIds, FakeStore
from tests.unit.application.services.requests.support import state_with_offer


def command(**overrides):
    values = dict(
        command_id="COMMAND-1",
        mission_id="MISSION-1",
        ship_id="SHIP-1",
        requested_seats=2,
        revision_id="REVISION-1",
        now=100,
        response_deadline=200,
    )
    return CreateRequest(**{**values, **overrides})


class CreateRequestTests(unittest.TestCase):
    """create_request opens a pending request inside one transaction.

    What: checks the applied, replayed and rejected results and what the store keeps.
    When called: by tests of the service behind RescueCentral.create_request.
    Why: a rejected command must leave the state untouched and a repeat must not draw ids.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.store = FakeStore(state_with_offer())
        self.ids = FakeIds()

    def run_create(self, cmd):
        return create_request(cmd, store=self.store, id_source=self.ids)

    def test_success_adds_a_pending_request(self):
        result = self.run_create(command())
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.request_id, "request-1")
        self.assertEqual(result.value.outcome, RequestOutcome.PENDING)
        self.assertEqual(len(self.store.state.missions[0].requests), 1)

    def test_replay_returns_the_stored_request_and_draws_no_id(self):
        first = self.run_create(command())
        second = self.run_create(command())
        self.assertEqual(second.status, "replayed")
        self.assertEqual(second.value, first.value)
        self.assertEqual(self.ids.counts["request"], 1)

    def test_same_command_id_with_other_payload_is_an_identity_conflict(self):
        self.run_create(command())
        result = self.run_create(command(requested_seats=3))
        self.assertEqual((result.status, result.reason), ("rejected", "identity_conflict"))

    def test_unknown_mission_is_rejected(self):
        result = self.run_create(command(mission_id="MISSION-9"))
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_mission"))

    def test_unknown_revision_is_rejected_and_state_is_kept(self):
        before = self.store.state
        result = self.run_create(command(revision_id="REVISION-9"))
        self.assertEqual((result.status, result.reason), ("rejected", "revision_conflict"))
        self.assertIs(self.store.state, before)

    def test_too_many_seats_is_rejected(self):
        result = self.run_create(command(requested_seats=7))
        self.assertEqual((result.status, result.reason), ("rejected", "insufficient_capacity"))

    def test_deadline_not_after_now_is_rejected(self):
        result = self.run_create(command(response_deadline=100))
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
