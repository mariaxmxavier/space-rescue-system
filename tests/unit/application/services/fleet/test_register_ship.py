"""Tests of the register_ship service.

What: proves a ship is registered once and bad or duplicate ships are rejected without a change.
When called: by pytest with the application unit tests.
Why: a ship must be known before it can publish availability or offers.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RegisterShip
from rescue.application.services.fleet.register_ship import register_ship
from tests.unit.application.services.fakes import FakeStore, empty_state


class RegisterShipTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore(empty_state())

    def test_applies_and_adds_the_ship_to_the_market(self):
        result = register_ship(RegisterShip("SHIP-1", "Rescue One"), store=self.store)

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.ship_id, "SHIP-1")
        self.assertEqual(self.store.state.market.ships, (result.value,))

    def test_rejects_a_duplicate_ship_as_identity_conflict(self):
        register_ship(RegisterShip("SHIP-1", "Rescue One"), store=self.store)
        before = self.store.state

        result = register_ship(RegisterShip("SHIP-1", "Other"), store=self.store)

        self.assertEqual((result.status, result.reason), ("rejected", "identity_conflict"))
        self.assertIs(self.store.state, before)

    def test_rejects_an_invalid_ship_without_changing_state(self):
        before = self.store.state

        result = register_ship(RegisterShip("", "Rescue One"), store=self.store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(self.store.state, before)
