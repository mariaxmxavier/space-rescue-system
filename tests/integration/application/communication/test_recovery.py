import unittest

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RecoverReports,
    RegisterMission,
    RegisterShip,
    SynchroniseInbound,
)
from rescue.bootstrap import new_run
from rescue.communication.models import (
    DecisionReport,
    FlowDirection,
    ReportCursor,
    SequenceControl,
    SessionEnvelope,
)
from rescue.communication.rules import receive_report
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision

SESSION = "S1"


def _setup():
    central = new_run("RUN-RECOVERY", "CENTRAL-RECOVERY").central
    central.register_mission(RegisterMission("MISSION-1", "Station", 3, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 4, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer("OFFER-1", "MISSION-1", "SHIP-1", ShipOfferRevision("REV-1", 1, 4, 5, True, 0))
    )
    request_ids = []
    for number in (1, 2):
        created = central.create_request(
            CreateRequest(
                command_id=f"COMMAND-{number}",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=1,
                revision_id="REV-1",
                now=0,
            )
        )
        request_ids.append(created.value.request_id)
    return central, request_ids


def _respond(central, request_id, number, sequence, outcome="accepted", confirmed=1):
    return central.record_response(
        RecordResponse(
            message_id=f"MSG-{number}",
            delivery_id=f"DEL-{number}",
            attempt_number=1,
            request_id=request_id,
            outcome=outcome,
            confirmed_seats=confirmed,
            sent_at=1,
            received_at=2,
            envelope=SessionEnvelope(SESSION, 1, FlowDirection.INBOUND, sequence),
        )
    )


def _with_two_reports():
    central, request_ids = _setup()
    _respond(central, request_ids[0], 1, 1)
    _respond(central, request_ids[1], 2, 2, outcome="refused", confirmed=0)
    return central


def _session(central):
    return central.get_session(SESSION).value


def _seats(central):
    progress = central.get_progress("MISSION-1", 100).value
    return progress.confirmed, progress.pending


class RecoverReportsTests(unittest.TestCase):
    def assert_rejected_without_change(self, command, reason):
        central = _with_two_reports()
        before = central.store.snapshot()

        result = central.recover_reports(command)

        self.assertEqual((result.status, result.reason), ("rejected", reason))
        self.assertEqual(central.store.snapshot(), before)

    def test_replays_original_reports_then_sequence_control_without_state_change(self):
        """Recovery replays the original reports then a SequenceControl and changes nothing."""
        central = _with_two_reports()
        original = _session(central).reports
        history = central.get_history("MISSION-1").value
        seats = _seats(central)
        before = central.store.snapshot()

        result = central.recover_reports(RecoverReports(SESSION, 1, 1, 2))

        self.assertEqual(result.status, "applied")
        *replayed, control = result.value
        self.assertEqual(len(original), 2)
        self.assertEqual(tuple(replayed), original)
        self.assertEqual(
            [(r.report_id, r.envelope.sequence) for r in replayed],
            [(r.report_id, r.envelope.sequence) for r in original],
        )
        self.assertEqual(
            control, SequenceControl(SESSION, 1, FlowDirection.OUTBOUND, len(original) + 1)
        )
        self.assertEqual(central.get_history("MISSION-1").value, history)
        self.assertEqual(_seats(central), seats)
        self.assertEqual(central.store.snapshot(), before)

    def test_replays_a_sub_range_with_original_identity(self):
        """A range inside the retained reports replays just those reports."""
        central = _with_two_reports()
        original = _session(central).reports

        result = central.recover_reports(RecoverReports(SESSION, 1, 2, 1))

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value[0], original[1])
        self.assertEqual(result.value[0].report_id, original[1].report_id)
        self.assertIsInstance(result.value[-1], SequenceControl)
        self.assertEqual(len(result.value), 2)

    def test_count_above_1000_is_recovery_limit_without_state_change(self):
        """A count of 1001 is rejected as recovery_limit and changes nothing."""
        self.assert_rejected_without_change(RecoverReports(SESSION, 1, 1, 1001), "recovery_limit")

    def test_range_beyond_retained_reports_is_out_of_range_without_state_change(self):
        """A range past the last retained report is rejected as recovery_out_of_range."""
        self.assert_rejected_without_change(
            RecoverReports(SESSION, 1, 2, 2), "recovery_out_of_range"
        )

    def test_inactive_session_version_is_stale_session_without_state_change(self):
        """An inactive session version is rejected as stale_session and changes nothing."""
        self.assert_rejected_without_change(RecoverReports(SESSION, 2, 1, 1), "stale_session")

    def test_unknown_session_is_rejected(self):
        """A session that does not exist is rejected as unknown_session."""
        central = _with_two_reports()

        result = central.recover_reports(RecoverReports("NO-SESSION", 1, 1, 1))

        self.assertEqual((result.status, result.reason), ("rejected", "unknown_session"))


class SynchroniseInboundTests(unittest.TestCase):
    def test_advance_records_a_not_applied_gap(self):
        """Advancing the inbound number records the skipped range as a NotApplied gap."""
        central = _with_two_reports()
        expected = _session(central).next_inbound

        result = central.synchronise_inbound(SynchroniseInbound(SESSION, 1, expected + 3))

        self.assertEqual(result.status, "applied")
        session = _session(central)
        self.assertEqual(session.next_inbound, expected + 3)
        self.assertEqual(session.gaps[-1].from_sequence, expected)
        self.assertEqual(session.gaps[-1].count, 3)

    def test_equal_number_is_a_no_op(self):
        """Synchronising to the current inbound number leaves the session unchanged."""
        central = _with_two_reports()
        before = central.store.snapshot()
        expected = _session(central).next_inbound

        result = central.synchronise_inbound(SynchroniseInbound(SESSION, 1, expected))

        self.assertEqual(result.status, "applied")
        self.assertEqual(central.store.snapshot(), before)

    def test_rewind_is_rejected_without_state_change(self):
        """Synchronising below the current inbound number is rejected as sequence_rewind."""
        central = _with_two_reports()
        before = central.store.snapshot()

        result = central.synchronise_inbound(SynchroniseInbound(SESSION, 1, 1))

        self.assertEqual((result.status, result.reason), ("rejected", "sequence_rewind"))
        self.assertEqual(central.store.snapshot(), before)


class ShipSideOrderingTests(unittest.TestCase):
    def test_ship_receives_reports_in_order_when_they_arrive_out_of_order(self):
        """The ship buffers report 2, recovers report 1 and then applies both in order."""
        central = _with_two_reports()
        first, second = _session(central).reports
        cursor = ReportCursor(SESSION, 1, 1)

        cursor, delivered, gap = receive_report(cursor, second)

        self.assertEqual(delivered, ())
        self.assertEqual(gap, (1, 1))
        self.assertEqual(cursor.buffered, (second,))
        self.assertEqual(cursor.next_expected, 1)

        recovered = central.recover_reports(RecoverReports(SESSION, 1, gap[0], gap[1]))
        self.assertEqual(recovered.status, "applied")
        replayed = [item for item in recovered.value if isinstance(item, DecisionReport)]
        self.assertEqual(replayed, [first])

        cursor, delivered, gap = receive_report(cursor, replayed[0])

        self.assertEqual(delivered, (first, second))
        self.assertIsNone(gap)
        self.assertEqual(cursor.next_expected, 3)
        self.assertEqual(cursor.buffered, ())

    def test_repeated_and_old_reports_have_no_further_effect(self):
        """A report that was already delivered returns the cursor unchanged."""
        central = _with_two_reports()
        first, _second = _session(central).reports
        cursor, delivered, _gap = receive_report(ReportCursor(SESSION, 1, 1), first)

        repeated_cursor, repeated, gap = receive_report(cursor, first)

        self.assertEqual(delivered, (first,))
        self.assertEqual(repeated, ())
        self.assertIsNone(gap)
        self.assertEqual(repeated_cursor, cursor)


if __name__ == "__main__":
    unittest.main()
