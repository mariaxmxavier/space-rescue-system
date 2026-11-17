"""Tests of the request_quotes service.

What: checks the RFQs created, the empty outcomes and each rejection.
When called: by pytest with the application unit tests; mirrors RescueCentral.request_quotes.
Why: every branch of the service is proved with fake ports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest
from dataclasses import replace

from rescue.application.contracts import RequestQuotes
from rescue.application.services.quotes.request_quotes import request_quotes
from tests.unit.application.services.fakes import FakeIds, FakeStore
from tests.unit.application.services.quotes.scenario import market_state


class RequestQuotesTests(unittest.TestCase):
    def call(self, state, command):
        store = FakeStore(state)
        ids = FakeIds()
        return store, ids, request_quotes(command, store=store, id_source=ids)

    def test_creates_one_pending_rfq_for_each_available_ship(self):
        store, _, result = self.call(market_state(), RequestQuotes("MISSION-1", 1, 20))

        self.assertEqual(result.status, "applied")
        self.assertEqual(len(result.value), 1)
        rfq = result.value[0]
        self.assertEqual((rfq.rfq_id, rfq.ship_id, rfq.requested_seats), ("rfq-1", "SHIP-1", 5))
        self.assertEqual(rfq.response_deadline, 20)
        self.assertEqual(store.state.market.rfqs, result.value)

    def test_asks_only_for_the_seats_the_ship_has_free(self):
        _, _, result = self.call(market_state(people_count=9), RequestQuotes("MISSION-1", 1))

        self.assertEqual(result.value[0].requested_seats, 6)

    def test_unknown_mission_is_rejected_and_nothing_is_published(self):
        state = market_state()
        store, _, result = self.call(state, RequestQuotes("MISSION-9", 1))

        self.assertEqual((result.status, result.reason), ("rejected", "unknown_mission"))
        self.assertIs(store.state, state)

    def test_deadline_not_after_now_is_invalid_input(self):
        state = market_state()
        store, ids, result = self.call(state, RequestQuotes("MISSION-1", 5, 5))

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)
        self.assertEqual(ids.counts["rfq"], 0)

    def test_bad_instant_is_rejected_as_invalid_input(self):
        state = market_state()
        store, _, result = self.call(state, RequestQuotes("MISSION-1", -1))

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, state)

    def test_no_available_ship_applies_with_no_rfq(self):
        store, _, result = self.call(market_state(available=False), RequestQuotes("MISSION-1", 1))

        self.assertEqual((result.status, result.value), ("applied", ()))
        self.assertEqual(store.state.market.rfqs, ())

    def test_ship_without_availability_is_skipped(self):
        state = market_state()
        bare = replace(state, market=replace(state.market, availabilities=()))

        _, _, result = self.call(bare, RequestQuotes("MISSION-1", 1))

        self.assertEqual((result.status, result.value), ("applied", ()))


if __name__ == "__main__":
    unittest.main()
