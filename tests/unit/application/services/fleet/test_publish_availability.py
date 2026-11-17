"""Tests of the publish_availability service.

What: proves availability is applied, replayed when unchanged, and rejected when invalid.
When called: by pytest with the application unit tests.
Why: quoting and mobilisation read the published availability of the fleet.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import PublishAvailability, RegisterShip
from rescue.application.services.fleet.publish_availability import publish_availability
from rescue.application.services.fleet.register_ship import register_ship
from rescue.market.models.availability import ShipAvailability
from tests.unit.application.services.fakes import FakeStore, empty_state


def availability(seats=6):
    return ShipAvailability(
        availability_id="AVAIL-1",
        ship_id="SHIP-1",
        total_seats=seats,
        arrival_estimate_seconds=10,
        available=True,
        recorded_at=0,
    )


class PublishAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore(empty_state())
        register_ship(RegisterShip("SHIP-1", "Rescue One"), store=self.store)

    def test_applies_a_new_availability(self):
        before = self.store.state

        result = publish_availability(PublishAvailability(availability()), store=self.store)

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value, availability())
        self.assertNotEqual(self.store.state.market, before.market)

    def test_replays_the_same_availability(self):
        publish_availability(PublishAvailability(availability()), store=self.store)
        before = self.store.state

        result = publish_availability(PublishAvailability(availability()), store=self.store)

        self.assertEqual(result.status, "replayed")
        self.assertEqual(self.store.state, before)

    def test_rejects_a_value_that_is_not_an_availability(self):
        before = self.store.state

        result = publish_availability(PublishAvailability("nope"), store=self.store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(self.store.state, before)

    def test_rejects_availability_of_an_unknown_ship(self):
        store = FakeStore(empty_state())

        result = publish_availability(PublishAvailability(availability()), store=store)

        self.assertEqual(result.status, "rejected")
        self.assertEqual(store.state, empty_state())
