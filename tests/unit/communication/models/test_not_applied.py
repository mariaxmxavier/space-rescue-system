"""Not applied notice tests."""

import unittest
from dataclasses import FrozenInstanceError

from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.values import DomainValidationError


def not_applied(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "from_sequence": 2,
        "count": 1,
    }
    return NotApplied(**(fields | overrides))


class NotAppliedTests(unittest.TestCase):
    def test_stores_the_session_version_and_missing_range(self):
        notice = not_applied()

        self.assertEqual(
            (notice.session_id, notice.version, notice.from_sequence, notice.count),
            ("local:ship-1", 1, 2, 1),
        )

    def test_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            not_applied().count = 2

    def test_equal_fields_make_equal_notices(self):
        self.assertEqual(not_applied(), not_applied())

    def test_session_id_must_be_nonblank(self):
        with self.assertRaisesRegex(DomainValidationError, "identifier must be a nonblank"):
            not_applied(session_id="  ")

    def test_version_must_be_positive(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            not_applied(version=0)

    def test_version_rejects_booleans(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            not_applied(version=True)

    def test_from_sequence_must_be_positive(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            not_applied(from_sequence=0)

    def test_count_must_be_positive(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            not_applied(count=0)
