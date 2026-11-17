import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import publish_availability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.inventory.rules import usage
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.market.models.offers.rules import publish_offer_revision
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import RFQOffer
from rescue.market.models.quotes.rules import close_quote, hold_quote, transfer_quote
from rescue.mission.models import Mission, SeatRequest


def availability(*, availability_id="availability-1", total_seats=6, recorded_at=1):
    return ShipAvailability(
        availability_id=availability_id,
        ship_id="ship-1",
        total_seats=total_seats,
        arrival_estimate_seconds=10,
        available=True,
        recorded_at=recorded_at,
    )


def rfq(*, rfq_id="rfq-1", status="pending"):
    return SeatRFQ(
        rfq_id=rfq_id,
        mission_id="mission-1",
        ship_id="ship-1",
        availability_id="availability-1",
        requested_seats=4,
        status=status,
        sent_at=1,
    )


def quote(*, offer_id="quote-1", rfq_id="rfq-1"):
    return RFQOffer(
        offer_id=offer_id,
        rfq_id=rfq_id,
        offered_seats=4,
        arrival_estimate_seconds=10,
        expires_at=30,
        recorded_at=2,
        status="held",
    )


def market(*, availabilities=None, rfqs=None, quotes=None, offers=()):
    return B3Market(
        market_id="market-1",
        ships=(Ship(ship_id="ship-1", name="Rescue One"),),
        availabilities=tuple(availabilities or (availability(),)),
        rfqs=tuple(rfqs or (rfq(),)),
        quotes=tuple(quotes or ()),
        offers=tuple(offers),
    )


def mission(*requests):
    return Mission(
        mission_id="mission-1",
        station_name="Station One",
        people_count=6,
        created_at=0,
        requests=tuple(requests),
    )


def request(*, outcome, requested_seats, confirmed_seats=0):
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=requested_seats,
        confirmed_seats=confirmed_seats,
        outcome=outcome,
        submitted_at=2,
        revision_id="revision-1",
    )


class MarketUsageTests(unittest.TestCase):
    def test_quote_hold_transfers_to_pending_then_counts_only_confirmed_seats(self):
        current_market = market()
        held_market = hold_quote(current_market, (), quote(), now=Decimal("2"))

        held = usage(held_market, (), "ship-1")
        self.assertEqual((held.total, held.held, held.pending, held.confirmed), (6, 4, 0, 0))
        self.assertEqual((held.used, held.free), (4, 2))

        transferred = transfer_quote(held_market, "quote-1", "request-1", now=Decimal("3"))
        pending_mission = mission(request(outcome="pending", requested_seats=4))
        pending = usage(transferred, (pending_mission,), "ship-1")
        self.assertEqual((pending.held, pending.pending, pending.confirmed), (0, 4, 0))
        self.assertEqual((pending.used, pending.free), (4, 2))
        with self.assertRaises(ValueError):
            transfer_quote(transferred, "quote-1", "request-2", now=Decimal("3"))

        confirmed_mission = mission(
            request(outcome="partially_accepted", requested_seats=4, confirmed_seats=3)
        )
        confirmed = usage(transferred, (confirmed_mission,), "ship-1")
        self.assertEqual((confirmed.held, confirmed.pending, confirmed.confirmed), (0, 0, 3))
        self.assertEqual((confirmed.used, confirmed.free), (3, 3))

    def test_only_one_quote_can_be_recorded_for_an_rfq_targeting_its_eligible_ship(self):
        availability_snapshot = availability()
        addressed_rfq = rfq()
        self.assertEqual(addressed_rfq.ship_id, "ship-1")
        self.assertEqual(addressed_rfq.availability_id, availability_snapshot.availability_id)

        current_market = market(availabilities=(availability_snapshot,), rfqs=(addressed_rfq,))
        held_market = hold_quote(current_market, (), quote(), now=Decimal("2"))

        with self.assertRaises(ValueError):
            hold_quote(held_market, (), quote(offer_id="quote-2"), now=Decimal("3"))

    def test_rejected_or_expired_quote_releases_its_unaccepted_hold(self):
        held_market = hold_quote(market(), (), quote(), now=Decimal("2"))

        for status in ("rejected", "expired"):
            with self.subTest(status=status):
                closed_at = Decimal("30") if status == "expired" else Decimal("3")
                closed_market = close_quote(held_market, "quote-1", status, now=closed_at)
                released = usage(closed_market, (), "ship-1")
                self.assertEqual((released.held, released.used, released.free), (0, 0, 6))

    def test_latest_availability_blocks_new_holds_without_erasing_direct_commitments(self):
        old_snapshot = availability(
            availability_id="availability-old", total_seats=6, recorded_at=1
        )
        latest_snapshot = availability(
            availability_id="availability-latest", total_seats=2, recorded_at=3
        )
        direct_commitment = request(outcome="pending", requested_seats=3)
        current_market = market(
            availabilities=(latest_snapshot, old_snapshot),
            rfqs=(rfq(),),
        )

        current_usage = usage(current_market, (mission(direct_commitment),), "ship-1")
        self.assertEqual((current_usage.total, current_usage.pending), (2, 3))
        self.assertEqual(
            (current_usage.used, current_usage.free, current_usage.shortfall), (3, 0, 1)
        )

        with self.assertRaises(ValueError):
            hold_quote(current_market, (mission(direct_commitment),), quote(), now=Decimal("4"))

        after_rejected_allocation = usage(current_market, (mission(direct_commitment),), "ship-1")
        self.assertEqual(
            (after_rejected_allocation.pending, after_rejected_allocation.used), (3, 3)
        )


class ShipOfferRevisionTests(unittest.TestCase):
    def test_current_revision_uses_highest_revision_number_not_recorded_time(self):
        older_number_but_later_timestamp = ShipOfferRevision(
            revision_id="revision-1",
            revision_number=1,
            capacity=6,
            arrival_estimate_seconds=10,
            available=True,
            recorded_at=20,
        )
        higher_number_but_earlier_timestamp = ShipOfferRevision(
            revision_id="revision-2",
            revision_number=2,
            capacity=4,
            arrival_estimate_seconds=12,
            available=True,
            recorded_at=10,
        )
        ship_offer = ShipOffer(
            offer_id="offer-1",
            mission_id="mission-1",
            ship_id="ship-1",
            revisions=(older_number_but_later_timestamp, higher_number_but_earlier_timestamp),
        )

        self.assertIs(ship_offer.current_revision, higher_number_but_earlier_timestamp)
        with self.assertRaises(FrozenInstanceError):
            higher_number_but_earlier_timestamp.capacity = 8

    def test_conflicting_availability_at_same_ship_time_is_rejected(self):
        current = market()
        conflicting = availability(
            availability_id="availability-conflict", total_seats=5, recorded_at=1
        )

        with self.assertRaises(ValueError):
            publish_availability(current, conflicting)

    def test_offer_revision_number_conflicts_do_not_rewrite_history(self):
        original = ShipOfferRevision(
            revision_id="revision-1",
            revision_number=1,
            capacity=6,
            arrival_estimate_seconds=10,
            available=True,
            recorded_at=1,
        )
        current = market(
            offers=(
                ShipOffer(
                    offer_id="offer-1",
                    mission_id="mission-1",
                    ship_id="ship-1",
                    revisions=(original,),
                ),
            )
        )
        conflicting = ShipOfferRevision(
            revision_id="revision-1b",
            revision_number=1,
            capacity=5,
            arrival_estimate_seconds=10,
            available=True,
            recorded_at=2,
        )

        with self.assertRaises(ValueError):
            publish_offer_revision(current, "offer-1", conflicting)
        self.assertIs(current.offers[0].current_revision, original)

    def test_quote_cannot_be_recorded_or_transferred_at_expiry(self):
        with self.assertRaises(ValueError):
            hold_quote(market(), (), quote(), now=Decimal("30"))

        held = hold_quote(market(), (), quote(), now=Decimal("2"))
        with self.assertRaises(ValueError):
            transfer_quote(held, "quote-1", "request-1", now=Decimal("30"))
        self.assertEqual(usage(held, (), "ship-1").held, 4)


if __name__ == "__main__":
    unittest.main()
