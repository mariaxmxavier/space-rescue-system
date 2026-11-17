"""Quote history and mission requests share the real memory publication boundary."""

import unittest
from dataclasses import replace

from rescue.application.contracts import (
    AcceptQuote,
    PublishAvailability,
    RecordQuote,
    RegisterMission,
    RegisterShip,
    RequestQuotes,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.inventory.rules import usage
from rescue.market.models.quotes import RFQOffer
from rescue.market.models.quotes.rules import transfer_quote
from rescue.mission.models import SeatRequest
from rescue.mission.rules import add_request
from rescue.values import TransitionContext


def _hold_quote(run, quote_id, now):
    rfqs = run.central.request_quotes(RequestQuotes("MISSION-1", now))
    assert rfqs.status == "applied"
    quote = RFQOffer(quote_id, rfqs.value[0].rfq_id, 3, 10, 30, now)
    assert run.central.record_quote(RecordQuote(quote, now)).status == "applied"


def _run_with_held_quote():
    run = new_run("RUN-HISTORY", "CENTRAL-HISTORY")
    assert (
        run.central.register_mission(RegisterMission("MISSION-1", "Station One", 6, 0)).status
        == "applied"
    )
    assert run.central.register_ship(RegisterShip("SHIP-1", "Rescue One")).status == "applied"
    assert (
        run.central.publish_availability(
            PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 6, 10, True, 0))
        ).status
        == "applied"
    )
    _hold_quote(run, "QUOTE-1", 1)
    return run


class MarketHistoryTransactionTests(unittest.TestCase):
    def test_failure_after_staging_preserves_persisted_run_and_all_history(self):
        run = _run_with_held_quote()
        accepted = run.central.accept_quote(AcceptQuote("ACCEPT-1", "MISSION-1", "QUOTE-1", 2))
        self.assertEqual(accepted.status, "applied")
        _hold_quote(run, "QUOTE-2", 3)
        before = run.store.snapshot()

        def fail_after_staging(state):
            request = SeatRequest(
                request_id="REQUEST-STAGED",
                command_id="COMMAND-STAGED",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                confirmed_seats=0,
                outcome="pending",
                submitted_at=4,
                quote_id="QUOTE-2",
            )
            mission = add_request(
                state.missions[0], request, TransitionContext("EVENT-STAGED", 4, "quote_accepted")
            )
            staged = replace(
                state,
                market=transfer_quote(state.market, "QUOTE-2", request.request_id, 4),
                missions=(mission,),
            )
            self.assertEqual(staged.market.quotes[-1].status, "accepted")
            self.assertEqual(staged.market.quote_history[-1].request_id, "REQUEST-STAGED")
            self.assertEqual(len(staged.missions[0].history), len(before.missions[0].history) + 1)
            raise RuntimeError("abort after staging quote acceptance")

        with self.assertRaisesRegex(RuntimeError, "abort after staging"):
            run.store.transact(fail_after_staging)

        after = run.store.snapshot()
        self.assertEqual(after, before)
        self.assertEqual(after.market.quote_history, before.market.quote_history)
        self.assertEqual(after.missions[0].history, before.missions[0].history)
        self.assertEqual(after.market.quotes[0].request_id, accepted.value.request_id)
        self.assertEqual(after.market.quotes[-1].status, "held")
        self.assertEqual(after.missions[0].requests, (accepted.value,))

    def test_acceptance_publishes_quote_history_and_pending_request_together(self):
        run = _run_with_held_quote()
        before = run.store.snapshot()

        accepted = run.central.accept_quote(AcceptQuote("ACCEPT-1", "MISSION-1", "QUOTE-1", 2))

        self.assertEqual(accepted.status, "applied")
        published = run.store.snapshot()
        quote = published.market.quotes[0]
        request = published.missions[0].requests[0]
        self.assertEqual(quote.status, "accepted")
        self.assertEqual(quote.request_id, request.request_id)
        self.assertEqual(request, accepted.value)
        self.assertEqual(
            (request.quote_id, request.outcome, request.requested_seats), ("QUOTE-1", "pending", 3)
        )
        self.assertEqual(published.market.quote_history[:-1], before.market.quote_history)
        change = published.market.quote_history[-1]
        self.assertEqual(
            (change.quote_id, change.status, change.changed_at, change.request_id),
            ("QUOTE-1", "accepted", 2, request.request_id),
        )
        self.assertEqual(len(published.missions[0].history), 1)
        entry = published.missions[0].history[0]
        self.assertEqual((entry.action, entry.pending_seats_delta), ("request_created", 3))
        inventory = usage(published.market, published.missions, "SHIP-1")
        self.assertEqual(
            (inventory.held, inventory.pending, inventory.used, inventory.free), (0, 3, 3, 3)
        )
        self.assertEqual(before.market.quotes[0].status, "held")
        self.assertEqual(before.missions[0].requests, ())
