"""Seeded run state for the mobilisation service tests.

What: builds a FakeStore holding one mission, one ship, one offer and one policy.
When called: by the mobilise and get_decision tests as their starting point.
Why: both tests need the same market without wiring the real services.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from rescue.application.contracts import (
    PublishAvailability,
    PublishOffer,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision
from rescue.mobilisation.models import MobilisationPolicy
from tests.unit.application.services.fakes import FakeStore

POLICY = MobilisationPolicy(
    policy_id="EARLIEST",
    revision=1,
    name="Earliest arrival",
    selection_criteria="earliest_arrival",
)


def seeded_store(with_offer: bool = True) -> FakeStore:
    run = new_run("RUN-1", "CENTRAL-1", policies=(POLICY,))
    central = run.central
    central.register_mission(RegisterMission("MISSION-1", "Station 1", 8, 0))
    if with_offer:
        central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
        central.publish_availability(
            PublishAvailability(availability=ShipAvailability("AVAIL-1", "SHIP-1", 6, 10, True, 0))
        )
        central.publish_offer(
            PublishOffer(
                offer_id="OFFER-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revision=ShipOfferRevision("REV-1", 1, 5, 10, True, 0),
            )
        )
    return FakeStore(run.store.transact(lambda state: (state, state)))
