import unittest

from rescue.application.contracts import (
    CancelRequest,
    CreateRequest,
    ExpireRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RecoverReports,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.communication.models import FlowDirection, SessionEnvelope
from rescue.market.models import ShipAvailability, ShipOfferRevision


def _setup(people=10, asks=(("SHIP-1", 6), ("SHIP-2", 4)), deadline=None):
    central = new_run("RUN-ORDER", "CENTRAL-ORDER").central
    central.register_mission(RegisterMission("MISSION-A", "Station", people, 0))
    requests = []
    for index, (ship, seats) in enumerate(asks, start=1):
        central.register_ship(RegisterShip(ship, ship))
        central.publish_availability(
            PublishAvailability(ShipAvailability(f"AV-{index}", ship, 10, 5, True, 0))
        )
        central.publish_offer(
            PublishOffer(
                f"OFFER-{index}",
                "MISSION-A",
                ship,
                ShipOfferRevision(f"REV-{index}", 1, 10, 5, True, 0),
            )
        )
        created = central.create_request(
            CreateRequest(
                command_id=f"CMD-{index}",
                mission_id="MISSION-A",
                ship_id=ship,
                requested_seats=seats,
                revision_id=f"REV-{index}",
                now=0,
                response_deadline=deadline,
            )
        )
        requests.append(created.value.request_id)
    return central, requests


def _respond(
    central,
    request_id,
    message,
    delivery,
    session=None,
    sequence=1,
    outcome="accepted",
    seats=1,
    sent_at=1,
    received_at=2,
    attempt=1,
):
    envelope = (
        None if session is None else SessionEnvelope(session, 1, FlowDirection.INBOUND, sequence)
    )
    return central.record_response(
        RecordResponse(
            message_id=message,
            delivery_id=delivery,
            attempt_number=attempt,
            request_id=request_id,
            outcome=outcome,
            confirmed_seats=seats,
            sent_at=sent_at,
            received_at=received_at,
            envelope=envelope,
        )
    )


def _numbers(central, mission="MISSION-A"):
    return [entry.mission_sequence for entry in central.get_history(mission).value]


def _confirmed(central):
    return central.get_progress("MISSION-A", 100).value.confirmed


def _reports(central, session):
    return central.get_session(session).value.reports


def _number(report):
    return report.mission_sequence


def _missing(reports):
    numbers = {r.mission_sequence for r in reports if r.mission_sequence is not None}
    return sorted(set(range(min(numbers), max(numbers) + 1)) - numbers)


def _expiry_race():
    central, (r1, _r2) = _setup(deadline=5)
    expired = central.expire_request(ExpireRequest("MISSION-A", r1, 6))
    late = _respond(central, r1, "MSG-S1", "DEL-S1", "S1", 1, seats=6, sent_at=3, received_at=8)
    return central, (expired, late)


def _confirmation_race():
    central, (r1, _r2) = _setup()
    first = _respond(central, r1, "MSG-A", "DEL-A", "S1", 1, seats=6, sent_at=3, received_at=4)
    second = _respond(central, r1, "MSG-B", "DEL-B", "S2", 1, seats=6, sent_at=3, received_at=4)
    return central, (first, second)


def _race():
    central, (r1, r2) = _setup()
    first = _respond(central, r2, "MSG-S2", "DEL-S2", "S2", 1, seats=4, sent_at=5, received_at=6)
    cancel = central.cancel_request(CancelRequest("MISSION-A", r1, 7, "operator"))
    late = _respond(central, r1, "MSG-S1", "DEL-S1", "S1", 1, seats=6, sent_at=3, received_at=8)
    duplicate = _respond(
        central, r2, "MSG-S2", "DEL-S2", "S2", 1, seats=4, sent_at=5, received_at=6
    )
    return central, (first, cancel, late, duplicate)


class MissionOrderTests(unittest.TestCase):
    def test_story_3_1_decisions_are_numbered_from_one_without_gaps(self):
        """The first decision is 1 and each following decision is one more."""
        central, (r1, r2) = _setup()
        self.assertEqual(_numbers(central), [1, 2])

        _respond(central, r1, "MSG-1", "DEL-1", "S1", 1, seats=6)
        self.assertEqual(_numbers(central), [1, 2, 3])
        _respond(central, r2, "MSG-2", "DEL-2", "S2", 1, seats=4)
        self.assertEqual(_numbers(central), [1, 2, 3, 4])

    def test_story_3_2_responses_take_effect_in_call_order(self):
        """Two responses apply in call order whatever their sent_at and session numbers."""
        central, (r1, r2) = _setup()

        _respond(central, r2, "MSG-2", "DEL-2", "S2", 1, seats=4, sent_at=50, received_at=60)
        _respond(central, r1, "MSG-1", "DEL-1", "S1", 9, seats=6, sent_at=1, received_at=70)

        history = central.get_history("MISSION-A").value
        self.assertEqual([entry.message_id for entry in history[2:]], ["MSG-2", "MSG-1"])
        self.assertEqual(_numbers(central), [1, 2, 3, 4])
        self.assertEqual(_confirmed(central), 10)

    def test_story_3_3_cancellation_races_late_confirmation(self):
        """The cancellation is 4 and the late confirmation is ignored after 4 with seats at 4."""
        central, (first, cancel, late, _duplicate) = _race()

        self.assertEqual(first.status, "applied")
        self.assertEqual(cancel.status, "applied")
        self.assertEqual((late.status, late.reason), ("ignored", "closed_request"))
        history = central.get_history("MISSION-A").value
        self.assertEqual(_numbers(central), [1, 2, 3, 4])
        self.assertEqual(history[3].reason, "operator")
        report = _reports(central, "S1")[-1]
        self.assertEqual(
            (report.mission_sequence, report.after_mission_sequence, report.reason),
            (None, 4, "closed_request"),
        )
        self.assertEqual(_confirmed(central), 4)

    def test_story_3_3_exact_duplicate_adds_no_history(self):
        """The exact duplicate of the S2 confirmation is ignored without history or seats."""
        central, (_first, _cancel, _late, duplicate) = _race()

        self.assertEqual(duplicate.status, "ignored")
        self.assertEqual(_numbers(central), [1, 2, 3, 4])
        self.assertEqual(_confirmed(central), 4)

    def test_story_3_5_retried_message_gets_a_new_place_and_keeps_its_id(self):
        """A retried message enters at the back of the order and keeps its message id."""
        central, (r1, r2) = _setup()
        _respond(central, r1, "MSG-1", "DEL-1", received_at=None, seats=6)
        _respond(central, r2, "MSG-2", "DEL-2", "S2", 1, seats=4)
        self.assertEqual(_numbers(central), [1, 2, 3])

        retry = _respond(central, r1, "MSG-1", "DEL-3", "S1", 1, seats=6, attempt=2, received_at=9)

        self.assertEqual(retry.status, "applied")
        history = central.get_history("MISSION-A").value
        self.assertEqual(_numbers(central), [1, 2, 3, 4])
        self.assertEqual([entry.message_id for entry in history[2:]], ["MSG-2", "MSG-1"])
        self.assertEqual(_reports(central, "S1")[-1].message_id, "MSG-1")

    def test_story_3_6_replay_duplicate_and_rejected_input_add_no_number(self):
        """A replay, an exact duplicate and a rejected input add no mission number."""
        central, (r1, r2) = _setup()
        _respond(central, r1, "MSG-1", "DEL-1", "S1", 1, seats=6)
        before = _numbers(central)

        duplicate = _respond(central, r1, "MSG-1", "DEL-1", "S1", 1, seats=6)
        replay = central.recover_reports(RecoverReports("S1", 1, 1, 1))
        rejected = _respond(central, r2, "MSG-9", "DEL-9", "S2", 1, seats=99)

        self.assertEqual(duplicate.status, "ignored")
        self.assertEqual(replay.status, "applied")
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(_numbers(central), before)
        self.assertEqual(_confirmed(central), 6)
        self.assertTrue(all(r.mission_sequence is None for r in _reports(central, "S2")))

    def test_story_3_7_history_rebuilds_from_reports_across_sessions(self):
        """One mission's numbers rebuild from the reports of two sessions."""
        central, _results = _race()

        reports = _reports(central, "S1") + _reports(central, "S2")
        numbered = sorted(r.mission_sequence for r in reports if r.mission_sequence is not None)

        self.assertEqual(numbered, [3])
        chain = {(r.after_mission_sequence, r.mission_sequence) for r in reports}
        self.assertEqual(chain, {(2, 3), (4, None)})

    def test_story_3_7_removed_report_is_a_visible_gap(self):
        """A report removed from the collected reports leaves its number missing from the chain."""
        central, (r1, r2, r3) = _setup(asks=(("SHIP-1", 3), ("SHIP-2", 3), ("SHIP-3", 3)))
        _respond(central, r1, "MSG-1", "DEL-1", "S1", 1, seats=3)
        _respond(central, r2, "MSG-2", "DEL-2", "S2", 1, seats=3)
        _respond(central, r3, "MSG-3", "DEL-3", "S1", 2, seats=3)
        reports = [r for s in ("S1", "S2") for r in _reports(central, s)]
        numbered = sorted((r for r in reports if r.mission_sequence is not None), key=_number)
        self.assertEqual(_missing(numbered), [])

        removed = numbered[1]
        kept = [r for r in reports if r is not removed]

        self.assertEqual(_missing(kept), [removed.mission_sequence])

    def test_sc_006_race_outcome_is_identical_in_twenty_runs(self):
        """Twenty runs of the race give identical numbers, reasons and seat totals."""
        seen = set()
        for _ in range(20):
            central, results = _race()
            report = _reports(central, "S1")[-1]
            seen.add(
                (
                    tuple(_numbers(central)),
                    _confirmed(central),
                    tuple((r.status, r.reason) for r in results),
                    (report.mission_sequence, report.after_mission_sequence),
                )
            )
        self.assertEqual(len(seen), 1)

    def test_sc_007_numbers_are_one_to_n_for_each_mission(self):
        """Each mission's numbers run 1..N with no gaps or reuse."""
        central, _results = _race()
        central.register_mission(RegisterMission("MISSION-B", "Other", 3, 0))
        central.publish_offer(
            PublishOffer(
                "OFFER-B", "MISSION-B", "SHIP-1", ShipOfferRevision("REV-B", 1, 10, 5, True, 0)
            )
        )
        created = central.create_request(
            CreateRequest("CMD-B", "MISSION-B", "SHIP-1", 3, "REV-B", 0, None)
        )
        _respond(central, created.value.request_id, "MSG-B", "DEL-B", "S1", 2, seats=3)

        for mission in ("MISSION-A", "MISSION-B"):
            numbers = _numbers(central, mission)
            self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_sc_006_expiry_against_late_response_is_identical_in_twenty_runs(self):
        """Twenty runs of expiry then a late response ignore it with identical numbers and seats."""
        seen = set()
        for _ in range(20):
            central, (expired, late) = _expiry_race()
            seen.add(
                (
                    (expired.status, late.status),
                    tuple(_numbers(central)),
                    _confirmed(central),
                    tuple(r.mission_sequence for r in _reports(central, "S1")),
                )
            )
        self.assertEqual(len(seen), 1)
        outcome = next(iter(seen))
        self.assertEqual(outcome[0], ("applied", "ignored"))
        self.assertEqual(outcome[2], 0)

    def test_sc_006_confirmation_against_confirmation_is_identical_in_twenty_runs(self):
        """Twenty runs of two confirmations for one request give identical numbers and seats."""
        seen = set()
        for _ in range(20):
            central, results = _confirmation_race()
            seen.add(
                (
                    tuple((r.status, r.reason) for r in results),
                    tuple(_numbers(central)),
                    _confirmed(central),
                )
            )
        self.assertEqual(len(seen), 1)
        outcome = next(iter(seen))
        self.assertEqual(outcome[0][0][0], "applied")
        self.assertEqual(outcome[0][1][0], "ignored")
        self.assertEqual(outcome[2], 6)
