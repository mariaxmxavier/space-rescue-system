import unittest
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import publish_availability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.offers.rules import publish_offer_revision
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import QuoteStatus, QuoteStatusChange, RFQOffer
from rescue.market.models.quotes.rules import close_quote, hold_quote, quote_history, transfer_quote


def market():
    return B3Market(
        market_id="market-1",
        ships=(Ship(ship_id="ship-1", name="Rescue One"),),
        availabilities=(
            ShipAvailability(
                availability_id="availability-1",
                ship_id="ship-1",
                total_seats=6,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=1,
            ),
        ),
        rfqs=tuple(
            SeatRFQ(
                rfq_id=rfq_id,
                mission_id="mission-1",
                ship_id="ship-1",
                availability_id="availability-1",
                requested_seats=2,
                status="pending",
                sent_at=1,
            )
            for rfq_id in ("rfq-1", "rfq-2")
        ),
    )


def quote(offer_id, rfq_id):
    return RFQOffer(
        offer_id=offer_id,
        rfq_id=rfq_id,
        offered_seats=2,
        arrival_estimate_seconds=10,
        expires_at=30,
        recorded_at=2,
    )


class QuoteHistoryTests(unittest.TestCase):
    def test_each_terminal_transition_records_exactly_one_change_with_request_only_on_acceptance(
        self,
    ):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        for status, instant, request_id in (
            (QuoteStatus.ACCEPTED, Decimal("4.125"), "request-1"),
            (QuoteStatus.REJECTED, Decimal("5.25"), None),
            (QuoteStatus.EXPIRED, Decimal("30"), None),
        ):
            with self.subTest(status=status):
                if status is QuoteStatus.ACCEPTED:
                    terminal = transfer_quote(held, "quote-1", request_id, now=instant)
                else:
                    terminal = close_quote(held, "quote-1", status, now=instant)

                expected = (
                    QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("2")),
                    QuoteStatusChange("quote-1", status, instant, request_id),
                )
                self.assertEqual(terminal.quote_history, expected)
                self.assertEqual(quote_history(terminal, "quote-1"), expected)
                self.assertEqual(terminal.quotes[0].status, status)
                self.assertEqual(terminal.quotes[0].request_id, request_id)
                for entry in terminal.quote_history:
                    self.assertEqual(
                        entry.request_id is not None, entry.status is QuoteStatus.ACCEPTED
                    )
                self.assertEqual(
                    held.quote_history,
                    (QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("2")),),
                )
                self.assertEqual(held.quotes[0].status, QuoteStatus.HELD)

    def test_each_successful_transition_appends_one_entry_in_order(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        held = hold_quote(held, (), quote("quote-2", "rfq-2"), now=Decimal("3"))
        accepted = transfer_quote(held, "quote-1", "request-1", now=Decimal("4"))
        closed = close_quote(accepted, "quote-2", "rejected", now=Decimal("5"))

        self.assertEqual(
            quote_history(closed, "quote-1"),
            (
                QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("2")),
                QuoteStatusChange("quote-1", QuoteStatus.ACCEPTED, Decimal("4"), "request-1"),
            ),
        )
        self.assertEqual(
            quote_history(closed, "quote-2"),
            (
                QuoteStatusChange("quote-2", QuoteStatus.HELD, Decimal("3")),
                QuoteStatusChange("quote-2", QuoteStatus.REJECTED, Decimal("5")),
            ),
        )
        self.assertEqual(len(closed.quote_history), 4)

    def test_refused_operation_adds_no_entry(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        with self.assertRaises(ValueError):
            transfer_quote(held, "quote-1", "request-1", now=Decimal("30"))
        self.assertEqual(len(held.quote_history), 1)
        self.assertEqual(quote_history(held, "unknown"), ())

    def test_refused_hold_and_premature_expiry_preserve_all_history(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        snapshot = replace(held)
        for operation in ("duplicate_hold", "premature_expiry"):
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    if operation == "duplicate_hold":
                        hold_quote(held, (), quote("quote-2", "rfq-1"), now=Decimal("3"))
                    else:
                        close_quote(held, "quote-1", QuoteStatus.EXPIRED, now=Decimal("29"))
                self.assertEqual(held, snapshot)
                self.assertEqual(
                    quote_history(held, "quote-1"),
                    (QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("2")),),
                )

    def test_terminal_outcomes_cannot_be_replaced_or_add_history(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        accepted = transfer_quote(held, "quote-1", "request-1", now=Decimal("4"))
        rejected = close_quote(held, "quote-1", QuoteStatus.REJECTED, now=Decimal("5"))
        expired = close_quote(held, "quote-1", QuoteStatus.EXPIRED, now=Decimal("30"))
        for terminal in (accepted, rejected, expired):
            snapshot = replace(terminal)
            for operation in ("transfer", "reject", "expire", "hold"):
                with self.subTest(status=terminal.quotes[0].status, operation=operation):
                    with self.assertRaises(ValueError):
                        if operation == "transfer":
                            transfer_quote(terminal, "quote-1", "request-2", now=Decimal("6"))
                        elif operation == "hold":
                            hold_quote(terminal, (), quote("quote-1", "rfq-1"), now=Decimal("6"))
                        else:
                            status = (
                                QuoteStatus.REJECTED
                                if operation == "reject"
                                else QuoteStatus.EXPIRED
                            )
                            close_quote(terminal, "quote-1", status, now=Decimal("30"))
                    self.assertEqual(terminal, snapshot)
                    self.assertEqual(len(terminal.quote_history), 2)

    def test_history_keeps_insertion_order_and_supplied_timestamps_across_quotes(self):
        first = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("10.5"))
        second = hold_quote(first, (), quote("quote-2", "rfq-2"), now=Decimal("3.25"))
        rejected = close_quote(second, "quote-2", QuoteStatus.REJECTED, now=Decimal("5.75"))
        accepted = transfer_quote(rejected, "quote-1", "request-1", now=Decimal("11.125"))

        self.assertEqual(
            accepted.quote_history,
            (
                QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("10.5")),
                QuoteStatusChange("quote-2", QuoteStatus.HELD, Decimal("3.25")),
                QuoteStatusChange("quote-2", QuoteStatus.REJECTED, Decimal("5.75")),
                QuoteStatusChange("quote-1", QuoteStatus.ACCEPTED, Decimal("11.125"), "request-1"),
            ),
        )
        self.assertEqual(
            quote_history(accepted, "quote-1"),
            (
                QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("10.5")),
                QuoteStatusChange("quote-1", QuoteStatus.ACCEPTED, Decimal("11.125"), "request-1"),
            ),
        )

    def test_quote_readback_keeps_insertion_order_when_closing_timestamp_is_earlier(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("10.5"))
        rejected = close_quote(held, "quote-1", QuoteStatus.REJECTED, now=Decimal("5.75"))

        self.assertEqual(
            quote_history(rejected, "quote-1"),
            (
                QuoteStatusChange("quote-1", QuoteStatus.HELD, Decimal("10.5")),
                QuoteStatusChange("quote-1", QuoteStatus.REJECTED, Decimal("5.75")),
            ),
        )

    def test_quote_history_entries_and_collection_are_immutable(self):
        held = hold_quote(market(), (), quote("quote-1", "rfq-1"), now=Decimal("2"))
        accepted = transfer_quote(held, "quote-1", "request-1", now=Decimal("4"))

        self.assertIsInstance(accepted.quote_history, tuple)
        with self.assertRaises(FrozenInstanceError):
            accepted.quote_history[1].status = QuoteStatus.REJECTED
        with self.assertRaises(FrozenInstanceError):
            accepted.quote_history = ()
        self.assertEqual(accepted.quote_history[1].status, QuoteStatus.ACCEPTED)
        self.assertEqual(accepted.quote_history[1].request_id, "request-1")

    def test_publications_append_immutable_histories_without_rewriting_earlier_markets(self):
        original = market()
        first_availability = original.availabilities[0]
        next_availability = replace(
            first_availability, availability_id="availability-2", total_seats=5, recorded_at=3
        )
        available = publish_availability(original, next_availability)
        first_revision = ShipOfferRevision(
            revision_id="revision-1",
            revision_number=1,
            capacity=5,
            arrival_estimate_seconds=10,
            available=True,
            recorded_at=Decimal("8"),
        )
        offered = publish_offer_revision(
            available, "offer-1", first_revision, mission_id="mission-1", ship_id="ship-1"
        )
        next_revision = replace(
            first_revision, revision_id="revision-2", revision_number=2, capacity=4, recorded_at=4
        )
        revised = publish_offer_revision(offered, "offer-1", next_revision)
        held = hold_quote(revised, (), quote("quote-1", "rfq-1"), now=Decimal("9"))
        accepted = transfer_quote(held, "quote-1", "request-1", now=Decimal("10"))

        self.assertEqual(original.availabilities, (first_availability,))
        self.assertEqual(original.offers, ())
        self.assertEqual(available.offers, ())
        self.assertEqual(offered.offers[0].revisions, (first_revision,))
        self.assertEqual(revised.quote_history, ())
        self.assertEqual(accepted.availabilities, (first_availability, next_availability))
        self.assertEqual(accepted.offers[0].revisions, (first_revision, next_revision))
        with self.assertRaises(FrozenInstanceError):
            accepted.availabilities[0].total_seats = 0
        with self.assertRaises(FrozenInstanceError):
            accepted.offers[0].revisions[0].capacity = 0
        self.assertEqual(accepted.availabilities[0].total_seats, 6)
        self.assertEqual(accepted.offers[0].revisions[0].capacity, 5)


if __name__ == "__main__":
    unittest.main()
