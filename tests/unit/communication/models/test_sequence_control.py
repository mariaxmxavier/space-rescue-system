"""Sequence control value tests."""

import dataclasses
import unittest

from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def sequence_control(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "direction": FlowDirection.OUTBOUND,
        "next_sequence": 1,
    }
    return SequenceControl(**(fields | overrides))


class SequenceControlTests(unittest.TestCase):
    def test_keeps_its_values(self):
        control = sequence_control()
        self.assertEqual(control.session_id, "local:ship-1")
        self.assertEqual(control.version, 1)
        self.assertIs(control.direction, FlowDirection.OUTBOUND)
        self.assertEqual(control.next_sequence, 1)

    def test_direction_accepts_member_or_string_value(self):
        self.assertIs(
            sequence_control(direction=FlowDirection.INBOUND).direction,
            FlowDirection.INBOUND,
        )
        self.assertIs(sequence_control(direction="inbound").direction, FlowDirection.INBOUND)

    def test_unknown_direction_is_rejected_with_its_value(self):
        with self.assertRaisesRegex(DomainValidationError, "unknown flow direction: 'sideways'"):
            sequence_control(direction="sideways")

    def test_blank_session_id_is_rejected(self):
        for session_id in ("", "   ", None):
            with self.subTest(session_id=session_id):
                with self.assertRaisesRegex(
                    DomainValidationError, "identifier must be a nonblank string"
                ):
                    sequence_control(session_id=session_id)

    def test_version_must_be_a_positive_integer(self):
        for version in (0, -1, True, 1.0, "1"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(
                    DomainValidationError, "version must be a positive integer"
                ):
                    sequence_control(version=version)

    def test_next_sequence_must_be_a_positive_integer(self):
        for next_sequence in (0, -3, False, 2.0, "1"):
            with self.subTest(next_sequence=next_sequence):
                with self.assertRaisesRegex(
                    DomainValidationError, "next_sequence must be a positive integer"
                ):
                    sequence_control(next_sequence=next_sequence)

    def test_is_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            sequence_control().version = 2


if __name__ == "__main__":
    unittest.main()
