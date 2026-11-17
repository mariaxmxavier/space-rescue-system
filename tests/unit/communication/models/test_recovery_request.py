"""Recovery request value tests."""

import dataclasses
import unittest

from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.values import DomainValidationError


def recovery_request(**overrides):
    fields = {
        "session_id": "session-1",
        "version": 2,
        "from_sequence": 3,
        "count": 4,
    }
    return RecoveryRequest(**(fields | overrides))


class RecoveryRequestTests(unittest.TestCase):
    def test_new_request_keeps_its_values(self):
        request = recovery_request()
        self.assertEqual(request.session_id, "session-1")
        self.assertEqual(request.version, 2)
        self.assertEqual(request.from_sequence, 3)
        self.assertEqual(request.count, 4)

    def test_blank_or_non_string_session_id_is_rejected(self):
        for session_id in ("", "   ", None, 7):
            with self.subTest(session_id=session_id):
                with self.assertRaisesRegex(
                    DomainValidationError, "identifier must be a nonblank string"
                ):
                    recovery_request(session_id=session_id)

    def test_version_must_be_a_positive_integer(self):
        for version in (0, -1, True, 1.0, "1"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(
                    DomainValidationError, "quantity must be a positive integer"
                ):
                    recovery_request(version=version)

    def test_from_sequence_must_be_a_positive_integer(self):
        for from_sequence in (0, -1, True, 1.0, "1"):
            with self.subTest(from_sequence=from_sequence):
                with self.assertRaisesRegex(
                    DomainValidationError, "quantity must be a positive integer"
                ):
                    recovery_request(from_sequence=from_sequence)

    def test_count_accepts_any_integer_so_the_rule_can_reject_it(self):
        for count in (-5, 0, 1, 1000, 1001):
            with self.subTest(count=count):
                self.assertEqual(recovery_request(count=count).count, count)

    def test_count_must_be_an_integer(self):
        for count in (True, 2.0, "2", None):
            with self.subTest(count=count):
                with self.assertRaisesRegex(DomainValidationError, "count must be an integer"):
                    recovery_request(count=count)

    def test_request_is_immutable(self):
        request = recovery_request()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.count = 5
