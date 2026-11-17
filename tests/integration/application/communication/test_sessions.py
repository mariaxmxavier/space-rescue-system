import unittest

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RegisterMission,
    RegisterShip,
    SynchroniseInbound,
)
from rescue.bootstrap import new_run
from rescue.communication.models import FlowDirection, NotApplied, SessionEnvelope
from rescue.market.models import ShipAvailability, ShipOfferRevision

SESSION = "SESSION-1"


def _setup(requests=4):
    central = new_run("RUN-SESSIONS", "CENTRAL-SESSIONS").central
    central.register_mission(RegisterMission("MISSION-1", "Station", requests, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 10, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer(
            "OFFER-1", "MISSION-1", "SHIP-1", ShipOfferRevision("REV-1", 1, 10, 5, True, 0)
        )
    )
    ids = []
    for index in range(requests):
        created = central.create_request(
            CreateRequest(
                command_id=f"COMMAND-{index}",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=1,
                revision_id="REV-1",
                now=0,
                response_deadline=None,
            )
        )
        ids.append(created.value.request_id)
    return central, ids


def _envelope(sequence, version=1):
    return SessionEnvelope(SESSION, version, FlowDirection.INBOUND, sequence)


def _send(central, request_id, message, sequence, *, version=1, delivery=None, **overrides):
    fields = {"sent_at": 1, "received_at": 2}
    fields.update(overrides)
    return central.record_response(
        RecordResponse(
            message_id=message,
            delivery_id=delivery or f"DEL-{message}-{sequence}-{version}",
            attempt_number=1,
            request_id=request_id,
            outcome="accepted",
            confirmed_seats=1,
            envelope=_envelope(sequence, version),
            **fields,
        )
    )


def _session(central):
    result = central.get_session(SESSION)
    return result.value if result.status == "applied" else result


def _seats(central):
    progress = central.get_progress("MISSION-1", 100).value
    return progress.confirmed, progress.pending


def _diagnostics(session):
    return (
        session.session_id,
        session.version,
        session.next_inbound,
        session.next_outbound,
        len(session.gaps),
        len(session.reports),
    )


class SessionSequencingTests(unittest.TestCase):
    def test_story1_both_directions_start_at_one_and_count_independently(self):
        """A new session version starts both counters at 1 and advances them independently."""
        central, ids = _setup()
        self.assertEqual(central.get_session(SESSION).reason, "unknown_session")

        _send(central, ids[0], "MSG-1", 1)

        session = _session(central)
        self.assertEqual(_diagnostics(session), (SESSION, 1, 2, 2, 0, 1))
        self.assertEqual(session.reports[0].envelope.sequence, 1)
        self.assertEqual(session.reports[0].envelope.direction, FlowDirection.OUTBOUND)

        _send(central, ids[1], "MSG-2", 2)
        _send(central, ids[1], "MSG-2", 1, received_at=3)

        self.assertEqual(_diagnostics(_session(central)), (SESSION, 1, 3, 3, 0, 2))

    def test_story2_inbound_three_while_two_expected_records_gap_and_applies(self):
        """Inbound 3 while 2 is expected gives NotApplied(2, 1) and message 3 is applied."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)

        result = _send(central, ids[1], "MSG-3", 3)

        self.assertEqual((result.status, result.reason), ("applied", None))
        session = _session(central)
        self.assertEqual(session.gaps, (NotApplied(SESSION, 1, 2, 1),))
        self.assertEqual((session.next_inbound, session.next_outbound), (4, 3))
        self.assertEqual(len(session.reports), 2)
        self.assertEqual(_seats(central), (2, 2))

    def test_story3_fresh_sequence_retry_confirms_once_and_delayed_old_is_ignored(self):
        """A fresh-sequence retry confirms once and a delayed lower sequence changes no seats."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)
        _send(central, ids[1], "MSG-3", 3)

        retried = _send(central, ids[2], "MSG-LOST", 4)
        seats = _seats(central)
        before = _diagnostics(_session(central))
        delayed = _send(central, ids[2], "MSG-LOST", 2)

        self.assertEqual((retried.status, retried.reason), ("applied", None))
        self.assertEqual((delayed.status, delayed.reason), ("ignored", "duplicate_sequence"))
        self.assertEqual(_seats(central), seats)
        self.assertEqual(seats, (3, 1))
        self.assertEqual(_diagnostics(_session(central)), before)
        last = central.get_deliveries("MSG-LOST").value[-1]
        self.assertEqual((last.disposition, last.reason), ("ignored", "duplicate_sequence"))

    def test_story5_resumed_session_keeps_counters(self):
        """A message on the same version continues the counters without reuse."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)
        _send(central, ids[1], "MSG-2", 2)

        _send(central, ids[2], "MSG-3", 3)

        self.assertEqual(_diagnostics(_session(central)), (SESSION, 1, 4, 4, 0, 3))

    def test_story5_higher_version_resets_counters(self):
        """A higher version restarts both counters, gaps and retained reports."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)
        _send(central, ids[1], "MSG-3", 3)

        _send(central, ids[2], "MSG-V2", 1, version=2)

        session = _session(central)
        self.assertEqual(_diagnostics(session), (SESSION, 2, 2, 2, 0, 1))
        self.assertEqual(session.reports[0].envelope.version, 2)

    def test_story5_lower_version_is_rejected_stale_and_publishes_nothing(self):
        """A lower version is rejected as stale_session and changes nothing."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1, version=2)
        session = _session(central)
        seats = _seats(central)

        result = _send(central, ids[1], "MSG-OLD", 5, version=1)

        self.assertEqual((result.status, result.reason), ("rejected", "stale_session"))
        self.assertEqual(_session(central), session)
        self.assertEqual(_seats(central), seats)
        self.assertEqual(central.get_deliveries("MSG-OLD").reason, "unknown_message")

    def test_story6_receipt_before_send_publishes_no_session_change(self):
        """A receipt before the send is rejected and creates or changes no session."""
        central, ids = _setup()

        first = _send(central, ids[0], "MSG-1", 1, sent_at=5, received_at=3)

        self.assertEqual((first.status, first.reason), ("rejected", "invalid_input"))
        self.assertEqual(central.get_session(SESSION).reason, "unknown_session")

        _send(central, ids[0], "MSG-2", 1)
        session = _session(central)
        second = _send(central, ids[1], "MSG-3", 2, sent_at=5, received_at=3)

        self.assertEqual((second.status, second.reason), ("rejected", "invalid_input"))
        self.assertEqual(_session(central), session)

    def test_story6_control_messages_consume_no_business_number(self):
        """Synchronising inbound records a gap and consumes no outbound number."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)
        before = _session(central)

        result = central.synchronise_inbound(SynchroniseInbound(SESSION, 1, 5))

        self.assertEqual(result.status, "applied")
        session = _session(central)
        self.assertEqual(session.gaps, (NotApplied(SESSION, 1, 2, 3),))
        self.assertEqual((session.next_inbound, session.next_outbound), (5, before.next_outbound))
        self.assertEqual(session.reports, before.reports)

    def test_edge_lost_inbound_send_does_not_advance_expected_number(self):
        """A send without receipt leaves the expected inbound number and creates no gap."""
        central, ids = _setup()
        _send(central, ids[0], "MSG-1", 1)
        before = _session(central)

        lost = _send(central, ids[1], "MSG-LOST", 2, received_at=None)

        self.assertEqual((lost.status, lost.reason), ("applied", None))
        self.assertEqual(_session(central), before)
        self.assertEqual(central.get_deliveries("MSG-LOST").value[-1].disposition, "lost")

        retried = _send(central, ids[1], "MSG-LOST", 2, delivery="DEL-RETRY", received_at=3)

        self.assertEqual((retried.status, retried.reason), ("applied", None))
        session = _session(central)
        self.assertEqual((session.next_inbound, session.gaps), (3, ()))


def _unsequenced(central, request_id, message, **overrides):
    fields = {
        "message_id": message,
        "delivery_id": f"DEL-{message}",
        "attempt_number": 1,
        "request_id": request_id,
        "outcome": "accepted",
        "confirmed_seats": 1,
        "sent_at": 1,
        "received_at": 2,
    }
    fields.update(overrides)
    return central.record_response(RecordResponse(**fields))


def _next_request_id(central):
    return central.id_source.next_id("request")


class UnsequencedCompatibilityTests(unittest.TestCase):
    def test_unsequenced_report_consumes_no_shared_id(self):
        """An unsequenced response's report takes no number from the shared id source."""
        baseline, _ids = _setup(requests=1)
        expected = _next_request_id(baseline)
        central, _ids = _setup(requests=1)

        recorded = _unsequenced(central, "REQUEST-UNKNOWN", "MSG-UNKNOWN")

        self.assertEqual(recorded.reason, "unknown_request")
        self.assertEqual(len(_session_of(central, "local:unknown").reports), 1)
        self.assertEqual(_next_request_id(central), expected)

    def test_unsequenced_response_follows_sequenced_session_version(self):
        """A default envelope uses the stored session's version, so it is not stale."""
        central, ids = _setup(requests=2)
        central.record_response(
            RecordResponse(
                message_id="MSG-V2",
                delivery_id="DEL-V2",
                attempt_number=1,
                request_id=ids[0],
                outcome="accepted",
                confirmed_seats=1,
                sent_at=1,
                received_at=2,
                envelope=SessionEnvelope("local:SHIP-1", 2, FlowDirection.INBOUND, 1),
            )
        )

        result = _unsequenced(central, ids[1], "MSG-PLAIN")

        self.assertEqual((result.status, result.reason), ("applied", None))
        self.assertEqual(_seats(central), (2, 0))
        session = _session_of(central, "local:SHIP-1")
        self.assertEqual((session.version, session.next_inbound), (2, 3))


def _session_of(central, session_id):
    return central.get_session(session_id).value


if __name__ == "__main__":
    unittest.main()
