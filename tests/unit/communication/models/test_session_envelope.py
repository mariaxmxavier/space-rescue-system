"""Session envelope value tests."""

import dataclasses
import unittest

from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def envelope(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "direction": "inbound",
        "sequence": 1,
    }
    return SessionEnvelope(**(fields | overrides))


class SessionEnvelopeTests(unittest.TestCase):
    def test_keeps_its_identity_fields(self):
        value = envelope(version=2, sequence=7, direction=FlowDirection.OUTBOUND)
        self.assertEqual(value.session_id, "local:ship-1")
        self.assertEqual(value.version, 2)
        self.assertEqual(value.sequence, 7)
        self.assertIs(value.direction, FlowDirection.OUTBOUND)

    def test_direction_accepts_member_or_string_value(self):
        self.assertIs(envelope(direction=FlowDirection.INBOUND).direction, FlowDirection.INBOUND)
        self.assertIs(envelope(direction="outbound").direction, FlowDirection.OUTBOUND)

    def test_unknown_direction_is_rejected_with_its_value(self):
        with self.assertRaisesRegex(DomainValidationError, "unknown flow direction: 'sideways'"):
            envelope(direction="sideways")

    def test_blank_session_id_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "identifier must be a nonblank string"):
            envelope(session_id="  ")

    def test_version_and_sequence_must_be_positive_integers(self):
        for field_name in ("version", "sequence"):
            for bad_value in (0, -1, True, 1.0, "1"):
                with self.subTest(field=field_name, value=bad_value):
                    with self.assertRaisesRegex(
                        DomainValidationError, "quantity must be a positive integer"
                    ):
                        envelope(**{field_name: bad_value})

    def test_envelope_is_immutable(self):
        value = envelope()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.sequence = 2


if __name__ == "__main__":
    unittest.main()
