"""error_reason_for tests."""

import unittest

from rescue.application.shared.error_reason_for import error_reason_for


class ErrorReasonForTests(unittest.TestCase):
    """error_reason_for maps an error message to a stable reason code.

    What: matches keywords in the message, first match wins, default invalid_input.
    When called: by tests of the shared mapper.
    Why: callers see reason codes, never raw domain messages.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_maps_each_keyword_to_its_reason(self):
        cases = {
            "Unknown mission X": "unknown_mission",
            "unknown ship X": "unknown_ship",
            "unknown request X": "unknown_request",
            "no demand left": "insufficient_demand",
            "capacity exceeded": "insufficient_capacity",
            "ship unavailable": "unavailable",
            "quote expired": "expired_quote",
            "stale revision": "revision_conflict",
            "request closed": "closed_request",
            "anything else": "invalid_input",
        }
        for message, reason in cases.items():
            with self.subTest(message=message):
                self.assertEqual(error_reason_for(ValueError(message)), reason)
