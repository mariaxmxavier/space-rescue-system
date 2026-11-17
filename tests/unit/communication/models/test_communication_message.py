"""Communication message model tests."""

import unittest
from decimal import Decimal

from rescue.communication.models.messages.communication_message import CommunicationMessage
from rescue.values import DomainValidationError


def make(**overrides):
    fields = {
        "message_id": "m1",
        "correlation_id": "c1",
        "kind": "reply",
        "payload": (("a", 1),),
        "sent_at": 5,
        "request_id": "r1",
    }
    return CommunicationMessage(**{**fields, **overrides})


class CommunicationMessageTests(unittest.TestCase):
    def test_valid_message_normalises_sent_at_and_payload(self):
        message = make(payload=[["a", Decimal("1.5")]], sent_at="5")

        self.assertEqual(message.sent_at, Decimal("5"))
        self.assertEqual(message.payload, (("a", Decimal("1.5")),))

    def test_blank_ids_are_rejected(self):
        for field in ("message_id", "correlation_id", "request_id"):
            with self.subTest(field=field), self.assertRaises(DomainValidationError):
                make(**{field: " "})

    def test_blank_or_non_string_kind_is_rejected(self):
        for kind in ("", "  ", 3):
            with (
                self.subTest(kind=kind),
                self.assertRaisesRegex(
                    DomainValidationError, "message kind must be a nonblank string"
                ),
            ):
                make(kind=kind)

    def test_str_and_bytes_payloads_are_rejected(self):
        for payload in ("ab", b"ab"):
            with (
                self.subTest(payload=payload),
                self.assertRaisesRegex(DomainValidationError, "collection of key/value pairs"),
            ):
                make(payload=payload)

    def test_non_pair_entries_are_rejected(self):
        for payload, message in (
            (("ab",), "key/value pair"),
            ((1,), "key/value pair"),
            ((("a", 1, 2),), "exactly two values"),
        ):
            with (
                self.subTest(payload=payload),
                self.assertRaisesRegex(DomainValidationError, message),
            ):
                make(payload=payload)

    def test_non_finite_decimal_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "primitive immutable values"):
            make(payload=(("a", Decimal("NaN")),))

    def test_non_iterable_payload_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "must be iterable"):
            make(payload=5)

    def test_message_is_frozen_and_hashable(self):
        message = make()

        with self.assertRaises(AttributeError):
            message.kind = "x"
        self.assertEqual(hash(message), hash(make()))
