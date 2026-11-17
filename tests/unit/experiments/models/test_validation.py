"""Private validation helpers of the experiment models."""

import unittest
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from rescue.experiments.models._validation import finite_tuple, frozen_tree
from rescue.values import DomainValidationError


class Color(Enum):
    RED = 1


@dataclass(frozen=True)
class Frozen:
    value: object


@dataclass
class Mutable:
    value: object


class FrozenTreeTests(unittest.TestCase):
    def test_scalars_enums_and_nested_tuples_are_frozen(self):
        self.assertTrue(frozen_tree((None, "a", 1, True, b"x", Decimal("1"), Color.RED, (1,))))

    def test_frozen_dataclass_of_frozen_parts_is_frozen(self):
        self.assertTrue(frozen_tree(Frozen((1, 2))))

    def test_mutable_parts_are_not_frozen(self):
        for value in ([], {}, Mutable(1), Frozen([]), (1, [2]), 1.5):
            with self.subTest(value=value):
                self.assertFalse(frozen_tree(value))


class FiniteTupleTests(unittest.TestCase):
    def test_list_and_tuple_become_a_tuple(self):
        self.assertEqual(finite_tuple([1, 2], "items"), (1, 2))
        self.assertEqual(finite_tuple((1,), "items"), (1,))

    def test_other_types_are_rejected(self):
        for value in ("abc", 1, None):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(
                    DomainValidationError, "items must be a finite tuple or list"
                ),
            ):
                finite_tuple(value, "items")


if __name__ == "__main__":
    unittest.main()
