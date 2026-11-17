import unittest
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from rescue.values import is_deeply_immutable


class Colour(Enum):
    RED = "red"


@dataclass(frozen=True)
class FrozenPair:
    left: object
    right: object


@dataclass
class MutablePair:
    left: object


class IsDeeplyImmutableTests(unittest.TestCase):
    def test_immutable_values_are_accepted(self):
        accepted = [
            None,
            "text",
            1,
            True,
            b"bytes",
            Decimal("1.5"),
            Colour.RED,
            (1, ("a", None)),
            FrozenPair(1, (Decimal("2"), Colour.RED)),
            FrozenPair(FrozenPair(None, "x"), ()),
        ]
        for value in accepted:
            with self.subTest(value=value):
                self.assertIs(is_deeply_immutable(value), True)

    def test_mutable_values_are_rejected(self):
        rejected = [
            MutablePair(1),
            FrozenPair([1], 2),
            FrozenPair(1, MutablePair(1)),
            [1, 2],
            (1, [2]),
            1.5,
            {"a": 1},
        ]
        for value in rejected:
            with self.subTest(value=value):
                self.assertIs(is_deeply_immutable(value), False)
