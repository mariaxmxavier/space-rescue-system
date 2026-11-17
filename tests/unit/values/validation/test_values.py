import unittest
from decimal import Decimal

from rescue import values


class IdentifierTests(unittest.TestCase):
    def test_ids_are_nonblank_strings_preserved_without_trimming_or_case_folding(self):
        for identifier in ("mission-1", "Mission-1", "  mission-1  "):
            with self.subTest(identifier=identifier):
                self.assertEqual(values.normalize_id(identifier), identifier)

    def test_ids_reject_empty_and_whitespace_only_values(self):
        for identifier in ("", " ", "\t\n"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(ValueError):
                    values.normalize_id(identifier)

    def test_ids_reject_non_string_values(self):
        for identifier in (None, 1, True, b"mission-1"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(ValueError):
                    values.normalize_id(identifier)


class QuantityTests(unittest.TestCase):
    def test_quantities_accept_only_exact_integer_inputs(self):
        self.assertEqual(values.normalize_quantity(7), 7)

        for quantity in (True, False, 7.0, 1.5, "7"):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    values.normalize_quantity(quantity)

    def test_nonnegative_seat_quantities_accept_zero_and_reject_negatives(self):
        self.assertEqual(values.normalize_nonnegative_quantity(0), 0)
        self.assertEqual(values.normalize_nonnegative_quantity(4), 4)

        for quantity in (-1, True, 1.5):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    values.normalize_nonnegative_quantity(quantity)

    def test_positive_seat_quantities_reject_zero(self):
        self.assertEqual(values.normalize_positive_quantity(1), 1)

        for quantity in (0, -1, True, 1.5):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    values.normalize_positive_quantity(quantity)


class InstantTests(unittest.TestCase):
    def test_integer_and_decimal_string_times_normalize_to_decimal(self):
        accepted = {
            0: Decimal("0"),
            12: Decimal("12"),
            "0": Decimal("0"),
            "0.125": Decimal("0.125"),
            "1e2": Decimal("1E+2"),
            Decimal("2.25"): Decimal("2.25"),
        }
        for input_value, expected in accepted.items():
            with self.subTest(input_value=input_value):
                result = values.normalize_instant(input_value)
                self.assertIsInstance(result, Decimal)
                self.assertEqual(result, expected)

    def test_times_reject_bool_float_negative_nonfinite_and_malformed_values(self):
        rejected = (
            True,
            False,
            0.0,
            1.25,
            -1,
            "-0.01",
            "NaN",
            "Infinity",
            "-Infinity",
            "not-a-time",
        )
        for input_value in rejected:
            with self.subTest(input_value=input_value):
                with self.assertRaises(ValueError):
                    values.normalize_instant(input_value)


class SnapshotCollectionTests(unittest.TestCase):
    def test_collection_inputs_are_copied_into_immutable_tuples(self):
        source = ["ship-1", "ship-2"]

        snapshot = values.immutable_tuple(source)

        self.assertIsInstance(snapshot, tuple)
        self.assertEqual(snapshot, ("ship-1", "ship-2"))
        source[0] = "changed"
        source.append("ship-3")
        self.assertEqual(snapshot, ("ship-1", "ship-2"))
        with self.assertRaises(TypeError):
            snapshot[0] = "changed"


if __name__ == "__main__":
    unittest.main()
