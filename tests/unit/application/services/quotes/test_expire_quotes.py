"""Tests of the expire_quotes service.

What: checks held quotes and pending RFQs past their time are expired and others kept.
When called: by pytest with the application unit tests; mirrors RescueCentral.expire_quotes.
Why: every branch of the service is proved with fake ports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.services.quotes.expire_quotes import expire_quotes
from tests.unit.application.services.fakes import FakeStore
from tests.unit.application.services.quotes.scenario import market_state, with_held_quote, with_rfq


class ExpireQuotesTests(unittest.TestCase):
    def test_expires_a_held_quote_at_its_expiry_instant(self):
        store = FakeStore(with_held_quote(market_state(), expires_at=30))

        result = expire_quotes(30, store=store)

        self.assertEqual((result.status, result.value), ("applied", ("QUOTE-1",)))
        self.assertEqual(store.state.market.quotes[0].status, "expired")

    def test_keeps_a_quote_before_its_expiry(self):
        store = FakeStore(with_held_quote(market_state(), expires_at=30))

        result = expire_quotes(29, store=store)

        self.assertEqual((result.status, result.value), ("applied", ()))
        self.assertEqual(store.state.market.quotes[0].status, "held")

    def test_expires_a_pending_rfq_past_its_deadline(self):
        store = FakeStore(with_rfq(market_state(), response_deadline=10))

        result = expire_quotes(10, store=store)

        self.assertEqual((result.status, result.value), ("applied", ("RFQ-1",)))
        self.assertEqual(store.state.market.rfqs[0].status, "expired")

    def test_keeps_an_rfq_without_deadline_or_not_pending(self):
        no_deadline = with_rfq(market_state())
        answered = with_rfq(market_state(), response_deadline=10, status="quoted")
        for start in (no_deadline, answered):
            store = FakeStore(start)

            result = expire_quotes(99, store=store)

            self.assertEqual(result.value, ())
            self.assertEqual(store.state.market.rfqs, start.market.rfqs)

    def test_a_bad_instant_is_rejected_and_nothing_is_published(self):
        state = with_held_quote(market_state())
        store = FakeStore(state)

        result = expire_quotes(-1, store=store)

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)


if __name__ == "__main__":
    unittest.main()
