"""expire_request service tests."""

import unittest

from rescue.application.contracts import ExpireRequest
from rescue.application.services.requests.expire_request import expire_request
from rescue.mission.models import RequestOutcome
from tests.unit.application.services.fakes import FakeIds, FakeStore
from tests.unit.application.services.requests.support import DEADLINE, state_with_pending_request


def command(**overrides):
    values = dict(mission_id="MISSION-1", request_id="REQUEST-1", now=DEADLINE)
    return ExpireRequest(**{**values, **overrides})


class ExpireRequestTests(unittest.TestCase):
    """expire_request closes a pending request once its deadline has passed.

    What: checks the applied, rejected and ignored results and the event id draw order.
    When called: by tests of the service behind RescueCentral.expire_request.
    Why: the original reads the instant and checks the deadline before it draws an event id.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.store = FakeStore(state_with_pending_request())
        self.ids = FakeIds()

    def run_expire(self, cmd):
        return expire_request(cmd, store=self.store, id_source=self.ids)

    def test_success_expires_the_request_at_the_deadline(self):
        result = self.run_expire(command())
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.outcome, RequestOutcome.EXPIRED)
        self.assertEqual(self.ids.counts["event"], 1)

    def test_before_the_deadline_is_rejected_without_an_event_id(self):
        before = self.store.state
        result = self.run_expire(command(now=DEADLINE - 1))
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertEqual(self.ids.counts["event"], 0)
        self.assertIs(self.store.state, before)

    def test_request_without_a_deadline_is_rejected(self):
        self.store.state = state_with_pending_request(deadline=None)
        result = self.run_expire(command())
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))

    def test_closed_request_is_ignored(self):
        self.run_expire(command())
        result = self.run_expire(command())
        self.assertEqual((result.status, result.reason), ("ignored", "closed_request"))

    def test_invalid_instant_draws_no_event_id(self):
        result = self.run_expire(command(now="not-an-instant"))
        self.assertEqual(result.status, "rejected")
        self.assertEqual(self.ids.counts["event"], 0)
