"""make_result tests."""

import unittest

from rescue.application.contracts import Result
from rescue.application.shared.make_result import make_result


class MakeResultTests(unittest.TestCase):
    """make_result builds a Result from a status, a value and a reason.

    What: wraps the Result constructor.
    When called: by tests of the shared builder.
    Why: every service returns its outcome through one builder.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_builds_a_result_with_the_given_fields(self):
        self.assertEqual(
            make_result("rejected", 7, "unknown_mission"),
            Result(status="rejected", value=7, reason="unknown_mission"),
        )

    def test_value_and_reason_default_to_none(self):
        result = make_result("applied")
        self.assertIsNone(result.value)
        self.assertIsNone(result.reason)
