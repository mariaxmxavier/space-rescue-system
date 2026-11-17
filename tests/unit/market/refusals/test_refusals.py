import unittest
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import latest_availability, publish_availability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.inventory.rules import usage
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.market.models.offers.rules import publish_offer_revision
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import QuoteStatusChange, RFQOffer
from rescue.market.models.quotes.rules import close_quote, hold_quote, transfer_quote
from rescue.mission.models import Mission, SeatRequest
from rescue.values import DomainValidationError


def mission(mission_id="mission-1", requests=()):
    return Mission(mission_id, "Station One", 6, 0, requests=requests)


def availability(availability_id="availability-1", **changes):
    values = dict(
        availability_id=availability_id,
        ship_id="ship-1",
        total_seats=6,
        arrival_estimate_seconds=10,
        available=True,
        recorded_at=1,
    )
    return ShipAvailability(**{**values, **changes})


def rfq(rfq_id="rfq-1", **changes):
    values = dict(
        rfq_id=rfq_id,
        mission_id="mission-1",
        ship_id="ship-1",
        availability_id="availability-1",
        requested_seats=4,
        status="pending",
        sent_at=1,
    )
    return SeatRFQ(**{**values, **changes})


def quote(offer_id="quote-1", **changes):
    values = dict(
        offer_id=offer_id,
        rfq_id="rfq-1",
        offered_seats=4,
        arrival_estimate_seconds=10,
        expires_at=30,
        recorded_at=2,
    )
    return RFQOffer(**{**values, **changes})


def revision(revision_id="revision-1", revision_number=1, **changes):
    values = dict(
        revision_id=revision_id,
        revision_number=revision_number,
        capacity=4,
        arrival_estimate_seconds=10,
        available=True,
        recorded_at=1,
    )
    return ShipOfferRevision(**{**values, **changes})


def offer(offer_id="offer-1", **changes):
    values = dict(offer_id=offer_id, mission_id="mission-1", ship_id="ship-1")
    return ShipOffer(**{**values, **changes, "revisions": changes.get("revisions", (revision(),))})


def market(**changes):
    values = dict(
        market_id="market-1",
        ships=(Ship(ship_id="ship-1", name="One"), Ship(ship_id="ship-2", name="Two")),
        availabilities=(availability(),),
        rfqs=(rfq(),),
    )
    return B3Market(**{**values, **changes})


HELD = hold_quote(market(), (), quote(), Decimal("2"))

REFUSALS = {
    "blank ship name": lambda: Ship(ship_id="ship-1", name=" "),
    "availability flag not boolean": lambda: availability(available=1),
    "RFQ deadline before sending": lambda: rfq(response_deadline=1),
    "quote expiry before recording": lambda: quote(expires_at=2),
    "accepted quote without request": lambda: quote(status="accepted"),
    "history entry names request when not accepted": lambda: QuoteStatusChange(
        "quote-1", "held", 1, "request-1"
    ),
    "revision flag not boolean": lambda: revision(available=0),
    "offer without revisions": lambda: offer(revisions=()),
    "offer with duplicate revision numbers": lambda: offer(
        revisions=(revision(), revision("revision-2"))
    ),
    "rule given a non-market": lambda: usage("market", (), "ship-1"),
    "latest availability of unknown ship": lambda: latest_availability(market(), "ship-9"),
    "two different snapshots at one instant": lambda: latest_availability(
        market(availabilities=(availability(), availability("availability-2", total_seats=2))),
        "ship-1",
    ),
    "publish a non-availability": lambda: publish_availability(market(), "availability"),
    "publish for unknown ship": lambda: publish_availability(
        market(), availability("availability-2", ship_id="ship-9")
    ),
    "publish reused availability id": lambda: publish_availability(
        market(), availability(total_seats=2)
    ),
    "usage with duplicate RFQ ids": lambda: usage(market(rfqs=(rfq(), rfq())), (), "ship-1"),
    "usage with duplicate quote ids": lambda: usage(
        replace(HELD, quotes=(*HELD.quotes, *HELD.quotes)), (), "ship-1"
    ),
    "usage with quote for unknown RFQ": lambda: usage(
        market(quotes=(quote(rfq_id="rfq-9"),)), (), "ship-1"
    ),
    "usage with duplicate missions": lambda: usage(market(), (mission(), mission()), "ship-1"),
    "publish a non-revision": lambda: publish_offer_revision(market(), "offer-1", "revision"),
    "duplicate offer ids": lambda: publish_offer_revision(
        market(offers=(offer(), offer(mission_id="mission-2"))), "offer-1", revision()
    ),
    "reused revision id with changed data": lambda: publish_offer_revision(
        market(offers=(offer(),)), "offer-1", revision(capacity=3)
    ),
    "reused revision number": lambda: publish_offer_revision(
        market(offers=(offer(),)), "offer-1", revision("revision-2")
    ),
    "new offer without mission and ship": lambda: publish_offer_revision(
        market(), "offer-1", revision()
    ),
    "second offer for one mission and ship": lambda: publish_offer_revision(
        market(offers=(offer(),)), "offer-2", revision(), mission_id="mission-1", ship_id="ship-1"
    ),
    "hold a non-quote": lambda: hold_quote(market(), (), "quote", Decimal("2")),
    "hold recorded in the future": lambda: hold_quote(market(), (), quote(), Decimal("1")),
    "hold an already accepted quote": lambda: hold_quote(
        market(), (), quote(status="accepted", request_id="request-1"), Decimal("2")
    ),
    "hold a reused quote id": lambda: hold_quote(
        replace(HELD, rfqs=(*HELD.rfqs, rfq("rfq-2"))), (), quote(rfq_id="rfq-2"), Decimal("2")
    ),
    "hold for unknown RFQ": lambda: hold_quote(market(), (), quote(rfq_id="rfq-9"), Decimal("2")),
    "hold above RFQ quantity": lambda: hold_quote(
        market(), (), quote(offered_seats=5), Decimal("2")
    ),
    "hold against missing snapshot": lambda: hold_quote(
        market(rfqs=(rfq(availability_id="availability-9"),)), (), quote(), Decimal("2")
    ),
    "hold when latest availability is off": lambda: hold_quote(
        market(
            availabilities=(
                availability(),
                availability("availability-2", recorded_at=2, available=False),
            )
        ),
        (),
        quote(),
        Decimal("2"),
    ),
    "transfer unknown quote": lambda: transfer_quote(HELD, "quote-9", "request-1", Decimal("3")),
    "transfer accepted quote": lambda: transfer_quote(
        transfer_quote(HELD, "quote-1", "request-1", Decimal("3")),
        "quote-1",
        "request-2",
        Decimal("4"),
    ),
    "close with an unknown status": lambda: close_quote(HELD, "quote-1", "accepted", Decimal("3")),
    "close an accepted quote": lambda: close_quote(
        transfer_quote(HELD, "quote-1", "request-1", Decimal("3")),
        "quote-1",
        "rejected",
        Decimal("4"),
    ),
    "expire before expiry": lambda: close_quote(HELD, "quote-1", "expired", Decimal("3")),
    "close before recording": lambda: close_quote(HELD, "quote-1", "rejected", Decimal("1")),
}


class RefusalTests(unittest.TestCase):
    def assert_refused_without_changes(self, current, attempt):
        before = deepcopy(current)
        history_before = deepcopy(current.quote_history)
        with self.assertRaises(DomainValidationError):
            attempt(current)
        self.assertEqual(current, before)
        self.assertEqual(current.quote_history, history_before)

    def test_excessive_hold_preserves_other_missions_holds_and_history(self):
        current = replace(
            HELD,
            rfqs=(*HELD.rfqs, rfq("rfq-2", mission_id="mission-2")),
        )
        self.assert_refused_without_changes(
            current,
            lambda value: hold_quote(
                value, (), quote("quote-2", rfq_id="rfq-2", offered_seats=3), Decimal("3")
            ),
        )
        inventory = usage(current, (), "ship-1")
        self.assertEqual((inventory.held, inventory.used, inventory.free), (4, 4, 2))

    def test_ship_without_availability_has_no_capacity_for_a_new_hold(self):
        current = market(availabilities=())
        inventory = usage(current, (), "ship-1")
        self.assertEqual((inventory.total, inventory.used, inventory.free), (0, 0, 0))
        self.assert_refused_without_changes(
            current, lambda value: hold_quote(value, (), quote(), Decimal("2"))
        )

    def test_duplicate_source_identities_are_refused_without_changes(self):
        cases = (
            (market(rfqs=(rfq(), rfq())), ()),
            (replace(HELD, quotes=(*HELD.quotes, *HELD.quotes)), ()),
            (HELD, (mission(), mission())),
        )
        for current, sources in cases:
            with self.subTest(market=current, sources=sources):
                self.assert_refused_without_changes(
                    current, lambda value: usage(value, sources, "ship-1")
                )

    def test_conflicting_same_time_publication_preserves_all_histories(self):
        current = replace(HELD, offers=(offer(),))
        self.assert_refused_without_changes(
            current,
            lambda value: publish_availability(
                value, availability("conflicting-publication", total_seats=2)
            ),
        )
        self.assertEqual(usage(current, (), "ship-1").free, 2)

    def test_second_quote_for_answered_rfq_is_refused_without_changes(self):
        self.assert_refused_without_changes(
            HELD, lambda value: hold_quote(value, (), quote("quote-2"), Decimal("3"))
        )
        self.assertEqual(usage(HELD, (), "ship-1").held, 4)

    def test_accepted_quote_refuses_repeated_transfer_and_close_without_changes(self):
        current = transfer_quote(HELD, "quote-1", "request-1", Decimal("3"))
        attempts = (
            lambda value: transfer_quote(value, "quote-1", "request-2", Decimal("4")),
            lambda value: close_quote(value, "quote-1", "rejected", Decimal("4")),
            lambda value: close_quote(value, "quote-1", "expired", Decimal("30")),
        )
        for attempt in attempts:
            with self.subTest(attempt=attempt):
                self.assert_refused_without_changes(current, attempt)

    def test_closed_quote_releases_only_its_seats_and_never_releases_twice(self):
        current = hold_quote(
            replace(HELD, rfqs=(*HELD.rfqs, rfq("rfq-2", mission_id="mission-2"))),
            (),
            quote("quote-2", rfq_id="rfq-2", offered_seats=1),
            Decimal("3"),
        )
        self.assertEqual(usage(current, (), "ship-1").held, 5)
        for status, instant in (("rejected", Decimal("4")), ("expired", Decimal("30"))):
            with self.subTest(status=status):
                closed = close_quote(current, "quote-1", status, instant)
                self.assertEqual(
                    closed.quote_history,
                    (*current.quote_history, QuoteStatusChange("quote-1", status, instant)),
                )
                inventory = usage(closed, (), "ship-1")
                self.assertEqual((inventory.held, inventory.used, inventory.free), (1, 1, 5))
                for attempted_status in ("rejected", "expired"):
                    self.assert_refused_without_changes(
                        closed,
                        lambda value: close_quote(
                            value, "quote-1", attempted_status, Decimal("31")
                        ),
                    )
                    self.assertEqual(usage(closed, (), "ship-1"), inventory)
                self.assert_refused_without_changes(
                    closed,
                    lambda value: transfer_quote(value, "quote-1", "request-1", Decimal("31")),
                )
                self.assertEqual(usage(closed, (), "ship-1"), inventory)

    def test_first_expiry_is_processed_after_late_transfer_is_refused(self):
        for instant in (Decimal("30"), Decimal("31")):
            with self.subTest(instant=instant):
                self.assert_refused_without_changes(
                    HELD,
                    lambda value: transfer_quote(value, "quote-1", "request-1", instant),
                )
                self.assertEqual(usage(HELD, (), "ship-1").held, 4)
                expired = close_quote(HELD, "quote-1", "expired", instant)
                self.assertEqual(expired.quotes[0].status, "expired")
                self.assertEqual(
                    expired.quote_history,
                    (*HELD.quote_history, QuoteStatusChange("quote-1", "expired", instant)),
                )
                inventory = usage(expired, (), "ship-1")
                self.assertEqual((inventory.held, inventory.used, inventory.free), (0, 0, 6))
                self.assert_refused_without_changes(
                    expired, lambda value: close_quote(value, "quote-1", "expired", instant)
                )
                self.assertEqual(usage(expired, (), "ship-1"), inventory)

    def test_each_invalid_value_or_transition_is_refused(self):
        for case, attempt in REFUSALS.items():
            with self.subTest(case=case), self.assertRaises(DomainValidationError):
                attempt()

    def test_replays_return_the_same_market(self):
        current = market(offers=(offer(),))
        self.assertIs(publish_availability(current, availability()), current)
        self.assertIs(publish_offer_revision(current, "offer-1", revision()), current)

    def test_offer_revisions_append_and_new_offers_start_with_one_revision(self):
        created = publish_offer_revision(
            market(), "offer-1", revision(), mission_id="mission-1", ship_id="ship-1"
        )
        revised = publish_offer_revision(created, "offer-1", revision("revision-2", 2))
        self.assertEqual([item.revision_number for item in revised.offers[0].revisions], [1, 2])
        self.assertEqual(revised.offers[0].current_revision.revision_id, "revision-2")

    def test_valid_deadline_and_other_ships_requests_are_accepted(self):
        self.assertEqual(rfq(response_deadline=5).response_deadline, Decimal("5"))
        other_ship = replace(rfq(), ship_id="ship-2")
        mixed = mission(
            requests=(
                SeatRequest(
                    request_id="other-ship-request",
                    command_id="other-ship-command",
                    mission_id="mission-1",
                    ship_id="ship-2",
                    requested_seats=1,
                    confirmed_seats=0,
                    outcome="pending",
                    submitted_at=1,
                ),
                SeatRequest(
                    request_id="refused-request",
                    command_id="refused-command",
                    mission_id="mission-1",
                    ship_id="ship-1",
                    requested_seats=2,
                    confirmed_seats=0,
                    outcome="refused",
                    submitted_at=1,
                    response_received_at=2,
                ),
            )
        )
        self.assertEqual(usage(market(rfqs=(other_ship,)), (mixed,), "ship-1").used, 0)
        self.assertIsNone(latest_availability(market(availabilities=()), "ship-2"))


if __name__ == "__main__":
    unittest.main()
