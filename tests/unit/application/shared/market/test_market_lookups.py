"""Market lookup helper tests."""

import unittest
from types import SimpleNamespace

from rescue.application.shared.find_offer_revision import find_offer_revision
from rescue.application.shared.find_quote import find_quote
from rescue.application.shared.find_rfq import find_rfq


class MarketLookupTests(unittest.TestCase):
    """The market lookups return the matching value, or None when the market has none.

    What: find_offer_revision, find_quote and find_rfq over a run's market.
    When called: by tests of the shared lookups.
    Why: services turn None into a rejection, so a miss must never raise.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.revision = SimpleNamespace(revision_id="REV-1")
        self.quote = SimpleNamespace(offer_id="QUOTE-1")
        self.rfq = SimpleNamespace(rfq_id="RFQ-1")
        offer = SimpleNamespace(mission_id="M-1", ship_id="S-1", revisions=(self.revision,))
        market = SimpleNamespace(offers=(offer,), quotes=(self.quote,), rfqs=(self.rfq,))
        self.state = SimpleNamespace(market=market)

    def test_find_offer_revision_returns_the_revision(self):
        self.assertIs(find_offer_revision(self.state, "M-1", "S-1", "REV-1"), self.revision)

    def test_find_offer_revision_misses_on_another_ship_or_revision(self):
        self.assertIsNone(find_offer_revision(self.state, "M-1", "S-2", "REV-1"))
        self.assertIsNone(find_offer_revision(self.state, "M-1", "S-1", "REV-2"))

    def test_find_quote_returns_the_quote_or_none(self):
        self.assertIs(find_quote(self.state, "QUOTE-1"), self.quote)
        self.assertIsNone(find_quote(self.state, "QUOTE-2"))

    def test_find_rfq_returns_the_rfq_or_none(self):
        self.assertIs(find_rfq(self.state, "RFQ-1"), self.rfq)
        self.assertIsNone(find_rfq(self.state, "RFQ-2"))
