import unittest

from rescue.market.models.procurement import RFQStatus, SeatRFQ
from rescue.market.models.quotes import QuoteStatus, QuoteStatusChange, RFQOffer
from rescue.values import DomainValidationError


def rfq(status):
    return SeatRFQ(
        rfq_id="rfq-1",
        mission_id="mission-1",
        ship_id="ship-1",
        availability_id="availability-1",
        requested_seats=2,
        status=status,
        sent_at=1,
    )


def quote(status, request_id=None):
    return RFQOffer(
        offer_id="quote-1",
        rfq_id="rfq-1",
        offered_seats=1,
        arrival_estimate_seconds=5,
        expires_at=10,
        recorded_at=1,
        status=status,
        request_id=request_id,
    )


def history_entry(status, request_id=None):
    return QuoteStatusChange(quote_id="quote-1", status=status, changed_at=2, request_id=request_id)


class StatusTests(unittest.TestCase):
    def test_rfq_construction_accepts_every_status_as_string_or_member(self):
        cases = (
            ("pending", RFQStatus.PENDING),
            ("quoted", RFQStatus.QUOTED),
            ("expired", RFQStatus.EXPIRED),
        )
        self.assertEqual(set(RFQStatus), {"pending", "quoted", "expired"})
        for old_string, member in cases:
            self.assertEqual(member, old_string)
            for supplied in (old_string, member):
                with self.subTest(status=supplied):
                    self.assertIs(rfq(supplied).status, member)

    def test_quote_and_history_construction_normalize_every_status(self):
        cases = (
            ("held", QuoteStatus.HELD, None),
            ("accepted", QuoteStatus.ACCEPTED, "request-1"),
            ("rejected", QuoteStatus.REJECTED, None),
            ("expired", QuoteStatus.EXPIRED, None),
        )
        self.assertEqual(set(QuoteStatus), {"held", "accepted", "rejected", "expired"})
        for old_string, member, request_id in cases:
            self.assertEqual(member, old_string)
            for construct in (quote, history_entry):
                for supplied in (old_string, member):
                    with self.subTest(entity=construct.__name__, status=supplied):
                        entity = construct(supplied, request_id)
                        self.assertIs(entity.status, member)
                        self.assertEqual(entity.request_id, request_id)

    def test_quote_and_history_acceptance_require_a_valid_request_id(self):
        for construct in (quote, history_entry):
            for request_id in (None, "", "   "):
                with self.subTest(entity=construct.__name__, request_id=request_id):
                    with self.assertRaises(DomainValidationError):
                        construct("accepted", request_id)

    def test_quote_and_history_other_statuses_refuse_linked_requests(self):
        for construct in (quote, history_entry):
            for status in ("held", "rejected", "expired"):
                with self.subTest(entity=construct.__name__, status=status):
                    with self.assertRaises(DomainValidationError):
                        construct(status, "request-1")

    def test_strings_become_named_statuses_that_still_equal_the_old_strings(self):
        pending = rfq("pending")
        self.assertIs(pending.status, RFQStatus.PENDING)
        self.assertEqual(pending.status, "pending")

        quote = RFQOffer(
            offer_id="quote-1",
            rfq_id="rfq-1",
            offered_seats=1,
            arrival_estimate_seconds=5,
            expires_at=10,
            recorded_at=1,
        )
        self.assertIs(quote.status, QuoteStatus.HELD)

    def test_unknown_statuses_are_refused(self):
        for construct in (rfq, quote, history_entry):
            for status in ("", "lost", "PENDING", "HELD"):
                with self.subTest(entity=construct.__name__, status=status):
                    with self.assertRaises(DomainValidationError):
                        construct(status)


if __name__ == "__main__":
    unittest.main()
