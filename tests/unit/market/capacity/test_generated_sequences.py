import random
import unittest
from dataclasses import replace
from decimal import Decimal

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import publish_availability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.inventory.rules import usage
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import RFQOffer
from rescue.market.models.quotes.rules import close_quote, hold_quote, transfer_quote
from rescue.mission.models import Mission, SeatRequest
from rescue.values import DomainValidationError

SEQUENCES = 200
RANDOM_STEPS = 40
SHIPS = ("ship-1", "ship-2")
MISSIONS = ("mission-1", "mission-2")


class Sequence:
    """Exercise market rules with real input values and a separate command ledger."""

    def __init__(self, seed, test):
        self.rng = random.Random(seed)
        self.test = test
        self.now = 0
        self.counter = 0
        self.trace = []
        self.events = set()
        self.market = B3Market(
            market_id="market-1",
            ships=tuple(Ship(ship_id=ship_id, name=ship_id) for ship_id in SHIPS),
        )
        self.missions = {
            mission_id: Mission(mission_id, mission_id, 1000, 0) for mission_id in MISSIONS
        }
        # Expected totals change only with command inputs, never production projections.
        self.ledger = {
            ship: {"total": 0, "held": 0, "pending": 0, "confirmed": 0, "available": False}
            for ship in SHIPS
        }
        self.snapshots = {}
        # These records are an oracle journal, not substitutes passed to market rules.
        self.holds = {}
        self.pending = {}

    def next_id(self, kind):
        self.counter += 1
        return f"{kind}-{self.counter}"

    def commitments(self):
        return tuple(self.missions.values())

    def step(self, action, *args):
        self.now += 1
        self.trace.append(f"t={self.now} {action}{args!r}")
        getattr(self, action)(*args)
        self.check()

    def publish(self, ship_id=None, total=None, available=None):
        ship_id = ship_id if ship_id is not None else self.rng.choice(SHIPS)
        total = total if total is not None else self.rng.randint(0, 8)
        available = available if available is not None else self.rng.random() > 0.2
        availability_id = self.next_id("availability")
        self.trace.append(f"publish {ship_id=} {total=} {available=}")
        self.market = publish_availability(
            self.market,
            ShipAvailability(
                availability_id=availability_id,
                ship_id=ship_id,
                total_seats=total,
                arrival_estimate_seconds=10,
                available=available,
                recorded_at=self.now,
            ),
        )
        if total < self.ledger[ship_id]["total"]:
            self.events.add("lowered availability")
        self.ledger[ship_id].update(total=total, available=available)
        self.snapshots[ship_id] = availability_id

    def hold(self, ship_id=None, mission_id=None, seats=None, lifetime=None):
        ship_id = ship_id if ship_id is not None else self.rng.choice(SHIPS)
        if ship_id not in self.snapshots:
            return
        mission_id = mission_id if mission_id is not None else self.rng.choice(MISSIONS)
        seats = seats if seats is not None else self.rng.randint(1, 5)
        lifetime = lifetime if lifetime is not None else self.rng.randint(1, 10)
        rfq = SeatRFQ(
            rfq_id=self.next_id("rfq"),
            mission_id=mission_id,
            ship_id=ship_id,
            availability_id=self.snapshots[ship_id],
            requested_seats=seats,
            status="pending",
            sent_at=self.now,
        )
        self.market = replace(self.market, rfqs=(*self.market.rfqs, rfq))
        quote_id = self.next_id("quote")
        quote = RFQOffer(
            offer_id=quote_id,
            rfq_id=rfq.rfq_id,
            offered_seats=seats,
            arrival_estimate_seconds=10,
            expires_at=self.now + lifetime,
            recorded_at=self.now,
        )
        ledger = self.ledger[ship_id]
        used = ledger["held"] + ledger["pending"] + ledger["confirmed"]
        fits = ledger["available"] and used + seats <= ledger["total"]
        self.trace.append(f"hold {ship_id=} {mission_id=} {seats=} {lifetime=} {fits=}")
        before = self.market
        try:
            result = hold_quote(before, self.commitments(), quote, Decimal(self.now))
        except DomainValidationError as error:
            self.trace.append(f"hold refused: {error}")
            self.test.assertFalse(fits, "a hold that fits was refused")
            self.test.assertIs(self.market, before)
            self.events.add("hold refused")
            return
        self.test.assertTrue(fits, "a hold that does not fit was accepted")
        self.market = result
        ledger["held"] += seats
        self.holds[quote_id] = (ship_id, mission_id, seats, self.now + lifetime)
        self.events.add("hold")

    def transfer(self):
        if not self.holds:
            return
        quote_id = self.rng.choice(tuple(self.holds))
        ship_id, mission_id, seats, expiry = self.holds[quote_id]
        request_id = self.next_id("request")
        self.trace.append(f"transfer {quote_id=} {request_id=}")
        before = self.market
        try:
            result = transfer_quote(before, quote_id, request_id, Decimal(self.now))
        except DomainValidationError as error:
            self.trace.append(f"transfer refused: {error}")
            self.test.assertGreaterEqual(self.now, expiry)
            self.test.assertIs(self.market, before)
            self.events.add("transfer refused")
            return
        self.test.assertLess(self.now, expiry, "an expired hold transferred")
        self.market = result
        request = SeatRequest(
            request_id=request_id,
            command_id=self.next_id("command"),
            mission_id=mission_id,
            ship_id=ship_id,
            requested_seats=seats,
            confirmed_seats=0,
            outcome="pending",
            submitted_at=self.now,
            quote_id=quote_id,
        )
        mission = self.missions[mission_id]
        self.missions[mission_id] = replace(mission, requests=(*mission.requests, request))
        self.ledger[ship_id]["held"] -= seats
        self.ledger[ship_id]["pending"] += seats
        del self.holds[quote_id]
        self.pending[request_id] = (ship_id, mission_id, seats)
        self.events.add("transfer")

    def close(self, status=None):
        if not self.holds:
            return
        quote_id = self.rng.choice(tuple(self.holds))
        ship_id, _, seats, expiry = self.holds[quote_id]
        status = status if status is not None else self.rng.choice(("expired", "rejected"))
        self.trace.append(f"close {quote_id=} {status=}")
        before = self.market
        try:
            result = close_quote(before, quote_id, status, Decimal(self.now))
        except DomainValidationError as error:
            self.trace.append(f"close refused: {error}")
            self.test.assertEqual(status, "expired")
            self.test.assertLess(self.now, expiry)
            self.test.assertIs(self.market, before)
            self.events.add("close refused")
            return
        if status == "expired":
            self.test.assertGreaterEqual(self.now, expiry, "a live hold expired early")
        self.market = result
        self.ledger[ship_id]["held"] -= seats
        del self.holds[quote_id]
        self.events.add(f"close {status}")

    def confirm(self, confirmed=None):
        if not self.pending:
            return
        request_id = self.rng.choice(tuple(self.pending))
        ship_id, mission_id, seats = self.pending[request_id]
        confirmed = confirmed if confirmed is not None else self.rng.randint(0, seats)
        outcome = (
            "refused"
            if confirmed == 0
            else "accepted"
            if confirmed == seats
            else "partially_accepted"
        )
        self.trace.append(f"response {request_id=} {confirmed=} {outcome=}")
        mission = self.missions[mission_id]
        self.missions[mission_id] = replace(
            mission,
            requests=tuple(
                replace(
                    request,
                    outcome=outcome,
                    confirmed_seats=confirmed,
                    response_received_at=self.now,
                    closed_at=self.now,
                )
                if request.request_id == request_id
                else request
                for request in mission.requests
            ),
        )
        self.ledger[ship_id]["pending"] -= seats
        self.ledger[ship_id]["confirmed"] += confirmed
        del self.pending[request_id]
        self.events.add(outcome)

    def check(self):
        for ship_id in SHIPS:
            ledger = self.ledger[ship_id]
            used = ledger["held"] + ledger["pending"] + ledger["confirmed"]
            expected = (
                ledger["total"],
                ledger["held"],
                ledger["pending"],
                ledger["confirmed"],
                used,
                max(0, ledger["total"] - used) if ledger["available"] else 0,
                max(0, used - ledger["total"]),
            )
            actual = usage(self.market, self.commitments(), ship_id)
            self.test.assertEqual(
                (
                    actual.total,
                    actual.held,
                    actual.pending,
                    actual.confirmed,
                    actual.used,
                    actual.free,
                    actual.shortfall,
                ),
                expected,
                f"independent seat ledger differs for {ship_id}",
            )


class GeneratedCapacitySequenceTests(unittest.TestCase):
    def test_no_seat_is_counted_twice_across_generated_sequences(self):
        for seed in range(SEQUENCES):
            sequence = Sequence(seed, self)
            try:
                self.assertTrue(
                    all(isinstance(mission, Mission) for mission in sequence.commitments()),
                    "generated capacity inputs must be real immutable missions",
                )
                # Every seed reaches the hard transitions before its random suffix.
                prefix = (
                    ("publish", SHIPS[0], 8, True),
                    ("publish", SHIPS[1], 8, True),
                    ("hold", SHIPS[0], MISSIONS[0], 3, 10),
                    ("transfer",),
                    ("publish", SHIPS[0], 1, True),
                    ("hold", SHIPS[0], MISSIONS[1], 1, 10),
                    ("confirm", 0),
                    ("hold", SHIPS[1], MISSIONS[1], 4, 10),
                    ("transfer",),
                    ("confirm", 2),
                    ("publish", SHIPS[0], 8, True),
                    ("hold", SHIPS[0], MISSIONS[0], 2, 10),
                    ("close", "expired"),
                    ("close", "rejected"),
                    ("hold", SHIPS[1], MISSIONS[0], 2, 1),
                    ("transfer",),
                    ("close", "expired"),
                )
                for action, *args in prefix:
                    sequence.step(action, *args)
                for _ in range(RANDOM_STEPS):
                    sequence.step(
                        sequence.rng.choice(
                            ("publish", "hold", "hold", "transfer", "close", "confirm")
                        )
                    )
                self.assertLessEqual(
                    {
                        "hold",
                        "hold refused",
                        "transfer",
                        "transfer refused",
                        "lowered availability",
                        "refused",
                        "partially_accepted",
                        "close refused",
                        "close rejected",
                        "close expired",
                    },
                    sequence.events,
                )
            except Exception as error:
                raise AssertionError(
                    f"seed={seed}\ntrace:\n" + "\n".join(sequence.trace) + f"\n{error}"
                ) from error


if __name__ == "__main__":
    unittest.main()
