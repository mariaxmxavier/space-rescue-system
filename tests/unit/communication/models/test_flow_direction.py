"""Flow direction vocabulary tests."""

import unittest

from rescue.communication.models.vocabulary.flow_direction import FlowDirection


class FlowDirectionTests(unittest.TestCase):
    def test_has_exactly_the_inbound_and_outbound_values(self):
        self.assertEqual(
            {direction.value for direction in FlowDirection},
            {"inbound", "outbound"},
        )

    def test_value_lookup_returns_the_member(self):
        self.assertIs(FlowDirection("inbound"), FlowDirection.INBOUND)

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            FlowDirection("sideways")


if __name__ == "__main__":
    unittest.main()
