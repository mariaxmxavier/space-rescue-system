"""Tests of the accept_quote service.

What: checks a held quote becomes a request, a repeat replays, and each refusal is reported.
When called: by pytest with the application unit tests; mirrors RescueCentral.accept_quote.
Why: every branch of the service is proved with fake ports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest
from dataclasses import replace

from rescue.application.contracts import AcceptQuote
from rescue.application.services.quotes.accept_quote import accept_quote
from tests.unit.application.services.fakes import FakeIds, FakeStore
from tests.unit.application.services.quotes.scenario import market_state, with_held_quote


class AcceptQuoteTests(unittest.TestCase):
    def setUp(self):
        self.state = with_held_quote(market_state())
        self.store = FakeStore(self.state)
        self.ids = FakeIds()

    def accept(self, command):
        return accept_quote(command, store=self.store, id_source=self.ids)

    def test_turns_a_held_quote_into_a_pending_request(self):
        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 2))

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.request_id, "request-1")
        self.assertEqual(result.value.quote_id, "QUOTE-1")
        self.assertEqual(self.store.state.market.quotes[0].status, "accepted")
        entry = self.store.state.command_index[0]
        self.assertEqual((entry[1], entry[2]), ("CMD-1", "accept_quote"))

    def test_the_same_command_replays_the_first_result(self):
        command = AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 2)
        first = self.accept(command)
        after_first = self.store.state

        again = self.accept(command)

        self.assertEqual((again.status, again.value), ("replayed", first.value))
        self.assertIs(self.store.state, after_first)
        self.assertEqual(self.ids.counts["request"], 1)

    def test_the_same_command_id_with_another_payload_is_an_identity_conflict(self):
        self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 2))
        after_first = self.store.state

        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 2, 50))

        self.assertEqual((result.status, result.reason), ("rejected", "identity_conflict"))
        self.assertIs(self.store.state, after_first)

    def test_unknown_quote_is_reported_as_expired(self):
        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-9", 2))

        self.assertEqual((result.status, result.reason), ("rejected", "expired_quote"))
        self.assertIs(self.store.state, self.state)

    def test_a_quote_of_another_mission_is_an_identity_conflict(self):
        result = self.accept(AcceptQuote("CMD-1", "MISSION-2", "QUOTE-1", 2))

        self.assertEqual((result.status, result.reason), ("rejected", "identity_conflict"))
        self.assertIs(self.store.state, self.state)

    def test_a_quote_without_its_rfq_is_an_identity_conflict(self):
        self.store.state = replace(self.state, market=replace(self.state.market, rfqs=()))
        before = self.store.state

        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 2))

        self.assertEqual((result.status, result.reason), ("rejected", "identity_conflict"))
        self.assertIs(self.store.state, before)

    def test_an_expired_quote_is_refused_and_closed_as_expired(self):
        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 30))

        self.assertEqual((result.status, result.reason), ("rejected", "expired_quote"))
        self.assertEqual(self.store.state.market.quotes[0].status, "expired")
        self.assertEqual(self.store.state.command_index, ())
        self.assertEqual(self.ids.counts["request"], 0)

    def test_a_request_the_domain_refuses_is_rejected_and_nothing_is_published(self):
        result = self.accept(AcceptQuote("CMD-1", "MISSION-1", "QUOTE-1", 5, 5))

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(self.store.state, self.state)

    def test_a_bad_command_is_invalid_input(self):
        result = self.accept(AcceptQuote("", "MISSION-1", "QUOTE-1", 2))

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(self.store.state, self.state)


if __name__ == "__main__":
    unittest.main()
