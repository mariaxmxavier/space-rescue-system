"""Tests of the record_quote service.

What: checks a held quote is stored and each rejection leaves the state alone.
When called: by pytest with the application unit tests; mirrors RescueCentral.record_quote.
Why: every branch of the service is proved with fake ports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RecordQuote
from rescue.application.services.quotes.record_quote import record_quote
from tests.unit.application.services.fakes import FakeStore
from tests.unit.application.services.quotes.scenario import market_state, quote, with_rfq


class RecordQuoteTests(unittest.TestCase):
    def test_holds_the_quote_for_a_known_rfq(self):
        store = FakeStore(with_rfq(market_state()))

        result = record_quote(RecordQuote(quote(), 1), store=store)

        self.assertEqual((result.status, result.value), ("applied", quote()))
        self.assertEqual(store.state.market.quotes, (quote(),))

    def test_a_value_that_is_not_a_quote_is_invalid_input(self):
        state = with_rfq(market_state())
        store = FakeStore(state)

        result = record_quote(RecordQuote("not a quote", 1), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)

    def test_unknown_rfq_is_invalid_input(self):
        state = market_state()
        store = FakeStore(state)

        result = record_quote(RecordQuote(quote(), 1), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)

    def test_an_expired_quote_is_rejected_as_expired_quote(self):
        state = with_rfq(market_state())
        store = FakeStore(state)

        result = record_quote(RecordQuote(quote(expires_at=5), 5), store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "expired_quote"))
        self.assertIs(store.state, state)


if __name__ == "__main__":
    unittest.main()
