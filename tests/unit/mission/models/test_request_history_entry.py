"""Request history entry tests."""

import unittest
from decimal import Decimal

from rescue.mission.models.mission.request_history_entry import RequestHistoryEntry
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.values import DomainValidationError


def history_entry(**overrides):
    fields = {
        "event_id": "event-1",
        "mission_sequence": 1,
        "recorded_at": "5",
        "action": "request_created",
        "confirmed_seats_delta": 0,
        "pending_seats_delta": 6,
        "reason": "request created",
        "message_id": None,
    }
    return RequestHistoryEntry(**(fields | overrides))


class RequestHistoryEntryTests(unittest.TestCase):
    def test_action_string_is_stored_as_history_action(self):
        entry = history_entry(action="request_created")

        self.assertIs(entry.action, HistoryAction.REQUEST_CREATED)

    def test_action_member_is_accepted(self):
        entry = history_entry(action=HistoryAction.REFUSED)

        self.assertIs(entry.action, HistoryAction.REFUSED)

    def test_unknown_action_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "unknown history action"):
            history_entry(action="pending")

    def test_blank_action_is_rejected_with_field_label(self):
        with self.assertRaisesRegex(DomainValidationError, "history action must be a nonblank"):
            history_entry(action="  ")

    def test_mission_sequence_must_be_positive(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            history_entry(mission_sequence=0)

    def test_mission_sequence_rejects_booleans(self):
        with self.assertRaisesRegex(DomainValidationError, "must be a positive integer"):
            history_entry(mission_sequence=True)

    def test_seat_deltas_may_be_negative(self):
        entry = history_entry(confirmed_seats_delta=-2, pending_seats_delta=-4)

        self.assertEqual((entry.confirmed_seats_delta, entry.pending_seats_delta), (-2, -4))

    def test_seat_deltas_must_be_integers(self):
        with self.assertRaisesRegex(
            DomainValidationError, "confirmed seats delta must be an integer"
        ):
            history_entry(confirmed_seats_delta=1.0)
        with self.assertRaisesRegex(
            DomainValidationError, "pending seats delta must be an integer"
        ):
            history_entry(pending_seats_delta=True)

    def test_reason_must_be_nonblank(self):
        with self.assertRaisesRegex(DomainValidationError, "history reason must be a nonblank"):
            history_entry(reason="")

    def test_message_id_is_optional_but_nonblank_when_given(self):
        self.assertIsNone(history_entry(message_id=None).message_id)
        self.assertEqual(history_entry(message_id="message-1").message_id, "message-1")
        with self.assertRaisesRegex(DomainValidationError, "message id must be a nonblank"):
            history_entry(message_id="  ")

    def test_event_id_must_be_nonblank(self):
        with self.assertRaisesRegex(DomainValidationError, "identifier must be a nonblank"):
            history_entry(event_id="")

    def test_recorded_at_normalises_decimal_and_text_to_the_same_instant(self):
        from_decimal = history_entry(recorded_at=Decimal("1.50"))
        from_text = history_entry(recorded_at="1.50")

        self.assertEqual(from_decimal.recorded_at, from_text.recorded_at)
