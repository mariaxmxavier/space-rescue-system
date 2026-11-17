"""DeliveryFacts tests."""

import unittest
from decimal import Decimal

from rescue.communication.models.deliveries.delivery_facts import DeliveryFacts
from rescue.values import DomainValidationError

FLAGS = (
    "delivery_known",
    "delivery_identical",
    "message_conflicts",
    "request_known",
    "request_open",
    "request_expired",
)


def facts(**overrides):
    values = dict(
        delivery_known=False,
        delivery_identical=False,
        message_conflicts=False,
        request_known=True,
        request_open=True,
        request_expired=False,
        submitted_at=1,
        deadline="20.5",
        sent_at=5,
        received_at=9,
    )
    values.update(overrides)
    return DeliveryFacts(**values)


class DeliveryFactsTests(unittest.TestCase):
    def test_instants_are_normalised_to_decimal(self):
        built = facts()

        self.assertEqual(built.submitted_at, Decimal("1"))
        self.assertEqual(built.deadline, Decimal("20.5"))
        self.assertEqual(built.sent_at, Decimal("5"))
        self.assertEqual(built.received_at, Decimal("9"))

    def test_optional_instants_may_be_none(self):
        built = facts(submitted_at=None, deadline=None, received_at=None)

        self.assertIsNone(built.submitted_at)
        self.assertIsNone(built.deadline)
        self.assertIsNone(built.received_at)

    def test_flags_reject_non_bool_values(self):
        for name in FLAGS:
            with self.subTest(name=name):
                with self.assertRaises(DomainValidationError):
                    facts(**{name: 1})

    def test_sent_at_is_required_and_validated(self):
        with self.assertRaises(DomainValidationError):
            facts(sent_at=None)
        with self.assertRaises(DomainValidationError):
            facts(sent_at=-1)

    def test_request_cannot_be_open_and_expired(self):
        with self.assertRaises(DomainValidationError):
            facts(request_open=True, request_expired=True)

    def test_unknown_request_is_neither_open_nor_expired(self):
        with self.assertRaises(DomainValidationError):
            facts(request_known=False, request_open=True, request_expired=False)
        with self.assertRaises(DomainValidationError):
            facts(request_known=False, request_open=False, request_expired=True)

    def test_unknown_request_with_no_state_is_valid(self):
        built = facts(request_known=False, request_open=False, request_expired=False)

        self.assertFalse(built.request_known)

    def test_is_frozen(self):
        with self.assertRaises(AttributeError):
            facts().request_open = False
