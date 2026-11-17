"""cancel_request service tests."""

import unittest

from rescue.application.contracts import CancelRequest
from rescue.application.services.requests.cancel_request import cancel_request
from rescue.mission.models import RequestOutcome
from tests.unit.application.services.fakes import FakeIds, FakeStore
from tests.unit.application.services.requests.support import state_with_pending_request


def command(**overrides):
    values = dict(
        mission_id="MISSION-1", request_id="REQUEST-1", now=150, reason="no longer needed"
    )
    return CancelRequest(**{**values, **overrides})


class CancelRequestTests(unittest.TestCase):
    """cancel_request closes a pending request as cancelled.

    What: checks the applied and ignored results and the event id draw order.
    When called: by tests of the service behind RescueCentral.cancel_request.
    Why: the original draws the event id before it reads the instant, and that order must stay.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.store = FakeStore(state_with_pending_request())
        self.ids = FakeIds()

    def run_cancel(self, cmd):
        return cancel_request(cmd, store=self.store, id_source=self.ids)

    def test_success_cancels_the_request(self):
        result = self.run_cancel(command())
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.outcome, RequestOutcome.CANCELLED)
        self.assertEqual(self.ids.counts["event"], 1)

    def test_closed_request_is_ignored(self):
        self.run_cancel(command())
        result = self.run_cancel(command())
        self.assertEqual((result.status, result.reason), ("ignored", "closed_request"))

    def test_invalid_instant_is_rejected_after_drawing_one_event_id(self):
        before = self.store.state
        result = self.run_cancel(command(now="not-an-instant"))
        self.assertEqual(result.status, "rejected")
        self.assertEqual(self.ids.counts["event"], 1)
        self.assertIs(self.store.state, before)

    def test_unknown_request_is_rejected(self):
        result = self.run_cancel(command(request_id="REQUEST-9"))
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_request"))
