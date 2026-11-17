"""Tests of the reject_quote service.

What: checks a held quote is closed as rejected and each refusal leaves the state alone.
When called: by pytest with the application unit tests; mirrors RescueCentral.reject_quote.
Why: every branch of the service is proved with fake ports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RejectQuote
from rescue.application.services.quotes.reject_quote import reject_quote
from tests.unit.application.services.fakes import FakeStore
from tests.unit.application.services.quotes.scenario import market_state, with_held_quote


class RejectQuoteTests(unittest.TestCase):
    def test_closes_a_held_quote_as_rejected(self):
        store = FakeStore(with_held_quote(market_state()))

        result = reject_quote(RejectQuote("QUOTE-1", 2), store=store)

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.status, "rejected")
        self.assertEqual(store.state.market.quotes[0].status, "rejected")

    def test_unknown_quote_is_reported_as_expired(self):
        state = market_state()
        store = FakeStore(state)

        result = reject_quote(RejectQuote("QUOTE-9", 2), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "expired_quote"))
        self.assertIs(store.state, state)

    def test_a_quote_no_longer_held_is_a_closed_request(self):
        store = FakeStore(with_held_quote(market_state()))
        reject_quote(RejectQuote("QUOTE-1", 2), store=store)
        before = store.state

        result = reject_quote(RejectQuote("QUOTE-1", 3), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "closed_request"))
        self.assertIs(store.state, before)

    def test_a_bad_instant_is_invalid_input(self):
        state = with_held_quote(market_state())
        store = FakeStore(state)

        result = reject_quote(RejectQuote("QUOTE-1", -1), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)


if __name__ == "__main__":
    unittest.main()
