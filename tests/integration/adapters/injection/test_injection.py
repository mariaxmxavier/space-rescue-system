"""Caller-supplied clock and ID source objects do not need to inherit their ports.

What: builds a run with plain objects that only have the port's method, then checks the central
holds those exact objects.

When: run by pytest with the integration suite.

Why: spec 003 edge case: any object with ``now()`` or ``next_id()`` is accepted. A future
``isinstance`` guard in the composition root would break such callers, and this test would catch it.
"""

import unittest

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision
from tests.integration.adapters.injection.doubles.plain_clock import PlainClock
from tests.integration.adapters.injection.doubles.plain_id_source import PlainIdSource


class InjectionTests(unittest.TestCase):
    """Checks that ``new_run`` wires plain objects through to the central unchanged.

    What: one test that builds a run with plain objects and asserts identity of each wired object.

    When: run by pytest with the integration suite.

    Why: guards the spec edge case that a caller-supplied port need not inherit its ABC.
    """

    def test_new_run_accepts_plain_objects_and_wires_them_unchanged(self):
        """Check that plain clock and ID source objects reach the run and the central unchanged.

        What: builds a run with ``PlainClock`` and ``PlainIdSource`` and asserts identity of each
        wired object on the run and on its central.

        When: run by pytest on every ``make test``.

        Why: a caller-supplied port must not need nominal inheritance from the ABC.
        """
        clock = PlainClock()
        id_source = PlainIdSource()

        run = new_run("RUN-1", "CENTRAL-1", clock=clock, id_source=id_source)

        self.assertIs(run.clock, clock)
        self.assertIs(run.id_source, id_source)
        self.assertIs(run.central.clock, clock)
        self.assertIs(run.central.id_source, id_source)

    def test_create_request_takes_its_id_from_the_plain_id_source(self):
        """Check that a request created through the central gets its ID from the injected source.

        What: registers one mission, ship and offer, creates a request and asserts the returned
        request ID is the one ``PlainIdSource`` produced and that it was asked for a ``request``.

        When: run by pytest on every ``make test``.

        Why: wiring by identity is not enough; the central must actually draw IDs from the source.
        """
        id_source = PlainIdSource()
        central = new_run("RUN-1", "CENTRAL-1", clock=PlainClock(), id_source=id_source).central
        central.register_mission(
            RegisterMission(
                mission_id="MISSION-1", station_name="Station 1", people_count=5, created_at=0
            )
        )
        central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
        central.publish_availability(
            PublishAvailability(
                availability=ShipAvailability(
                    availability_id="AVAIL-1",
                    ship_id="SHIP-1",
                    total_seats=6,
                    arrival_estimate_seconds=10,
                    available=True,
                    recorded_at=0,
                )
            )
        )
        central.publish_offer(
            PublishOffer(
                offer_id="OFFER-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revision=ShipOfferRevision(
                    revision_id="REV-1",
                    revision_number=1,
                    capacity=6,
                    arrival_estimate_seconds=10,
                    available=True,
                    recorded_at=0,
                ),
            )
        )

        result = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                revision_id="REV-1",
                now=1,
            )
        )

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.request_id, "request-plain")
        self.assertIn("request", id_source.kinds)


if __name__ == "__main__":
    unittest.main()
