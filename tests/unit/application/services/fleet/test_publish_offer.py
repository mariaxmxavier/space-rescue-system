"""Tests of the publish_offer service.

What: proves an offer revision is applied, replayed, or rejected for each reason the service returns.
When called: by pytest with the application unit tests.
Why: a ship states what it can carry one revision at a time, and a refused revision must change nothing.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import dataclasses
import unittest

from rescue.application.contracts import PublishOffer, RegisterShip
from rescue.application.services.fleet.publish_offer import publish_offer
from rescue.application.services.fleet.register_ship import register_ship
from rescue.market.models.offers import ShipOfferRevision
from rescue.mission import rules as mission_rules
from rescue.mission.models import MissionData
from tests.unit.application.services.fakes import FakeStore, empty_state


def revision(revision_id="REV-1", capacity=6):
    return ShipOfferRevision(
        revision_id=revision_id,
        revision_number=1,
        capacity=capacity,
        arrival_estimate_seconds=10,
        available=True,
        recorded_at=0,
    )


def command(offer_id="OFFER-1", mission_id="MISSION-1", ship_id="SHIP-1", rev=None):
    return PublishOffer(offer_id, mission_id, ship_id, rev if rev is not None else revision())


class PublishOfferTests(unittest.TestCase):
    def setUp(self):
        mission = mission_rules.register(MissionData("MISSION-1", "Station", 5, 0))
        state = dataclasses.replace(empty_state(), missions=(mission,))
        self.store = FakeStore(state)
        register_ship(RegisterShip("SHIP-1", "Rescue One"), store=self.store)

    def assert_rejected(self, result, reason, before):
        self.assertEqual((result.status, result.reason), ("rejected", reason))
        self.assertIs(self.store.state, before)

    def test_applies_a_first_revision_and_returns_the_offer(self):
        result = publish_offer(command(), store=self.store)

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.offer_id, "OFFER-1")
        self.assertEqual(self.store.state.market.offers, (result.value,))

    def test_replays_the_same_revision(self):
        publish_offer(command(), store=self.store)
        before = self.store.state

        result = publish_offer(command(), store=self.store)

        self.assertEqual(result.status, "replayed")
        self.assertEqual(result.value.offer_id, "OFFER-1")
        self.assertIs(self.store.state, before)

    def test_rejects_an_unknown_mission(self):
        before = self.store.state
        result = publish_offer(command(mission_id="MISSION-9"), store=self.store)
        self.assert_rejected(result, "unknown_mission", before)

    def test_rejects_an_unknown_ship(self):
        before = self.store.state
        result = publish_offer(command(ship_id="SHIP-9"), store=self.store)
        self.assert_rejected(result, "unknown_ship", before)

    def test_rejects_a_value_that_is_not_a_revision(self):
        before = self.store.state
        result = publish_offer(command(rev="nope"), store=self.store)
        self.assert_rejected(result, "revision_conflict", before)

    def test_rejects_an_offer_id_reused_for_another_ship(self):
        publish_offer(command(), store=self.store)
        register_ship(RegisterShip("SHIP-2", "Rescue Two"), store=self.store)
        before = self.store.state

        result = publish_offer(command(ship_id="SHIP-2", rev=revision("REV-2")), store=self.store)

        self.assert_rejected(result, "identity_conflict", before)

    def test_rejects_a_changed_revision_under_a_published_revision_id(self):
        publish_offer(command(), store=self.store)
        before = self.store.state

        result = publish_offer(command(rev=revision(capacity=3)), store=self.store)

        self.assert_rejected(result, "revision_conflict", before)

    def test_rejects_a_revision_id_published_under_another_offer(self):
        publish_offer(command(), store=self.store)
        before = self.store.state

        result = publish_offer(command(offer_id="OFFER-2"), store=self.store)

        self.assert_rejected(result, "revision_conflict", before)
