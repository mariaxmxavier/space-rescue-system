"""Public application DTO and result contracts."""

import unittest
from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass
from inspect import Parameter, signature

from rescue.application import contracts

COMMAND_FIELDS = {
    "RegisterMission": ({"mission_id", "station_name", "people_count", "created_at"}, set()),
    "RegisterShip": ({"ship_id", "name"}, set()),
    "PublishAvailability": ({"availability"}, set()),
    "PublishOffer": ({"offer_id", "mission_id", "ship_id", "revision"}, set()),
    "RequestQuotes": ({"mission_id", "now"}, {"response_deadline"}),
    "RecordQuote": ({"offer", "now"}, set()),
    "AcceptQuote": (
        {"command_id", "mission_id", "quote_id", "now"},
        {"response_deadline", "decision_id", "revision_id"},
    ),
    "CreateRequest": (
        {"command_id", "mission_id", "ship_id", "requested_seats", "revision_id", "now"},
        {"response_deadline", "decision_id"},
    ),
    "RejectQuote": ({"quote_id", "now"}, set()),
    "RecordResponse": (
        {
            "message_id",
            "delivery_id",
            "attempt_number",
            "request_id",
            "outcome",
            "confirmed_seats",
            "sent_at",
            "received_at",
        },
        {"communication_rtt_seconds", "envelope"},
    ),
    "RecoverReports": ({"session_id", "version", "from_sequence", "count"}, set()),
    "SynchroniseInbound": ({"session_id", "version", "next_sequence"}, set()),
    "CancelRequest": ({"mission_id", "request_id", "now", "reason"}, set()),
    "ExpireRequest": ({"mission_id", "request_id", "now"}, set()),
    "Mobilise": ({"mission_id", "policy_id", "policy_revision", "now"}, set()),
    "ComparePolicies": ({"scenario_id", "scenario_revision", "policy_keys"}, set()),
}

RESULT_STATUSES = ("applied", "replayed", "rejected", "ignored")
RESULT_REASONS = (
    "invalid_input",
    "unknown_mission",
    "unknown_ship",
    "unknown_request",
    "unknown_decision",
    "unknown_message",
    "identity_conflict",
    "closed_request",
    "late",
    "insufficient_demand",
    "insufficient_capacity",
    "unavailable",
    "expired_quote",
    "revision_conflict",
)
SEQUENCING_RESULT_REASONS = (
    "duplicate_sequence",
    "stale_session",
    "sequence_rewind",
    "recovery_out_of_range",
    "recovery_limit",
    "recovery_in_progress",
    "unknown_session",
)


class CommandContractTests(unittest.TestCase):
    def test_every_command_is_a_frozen_dataclass_with_contract_fields(self):
        for command_name, (required, optional) in COMMAND_FIELDS.items():
            with self.subTest(command=command_name):
                command = getattr(contracts, command_name)
                self.assertTrue(is_dataclass(command))
                self.assertTrue(command.__dataclass_params__.frozen)

                command_fields = {field.name: field for field in fields(command)}
                self.assertEqual(set(command_fields), required | optional)
                for field_name in required:
                    self.assertIs(command_fields[field_name].default, MISSING)
                for field_name in optional:
                    self.assertIsNone(command_fields[field_name].default)

                parameters = signature(command).parameters.values()
                self.assertFalse(
                    any(parameter.kind is Parameter.VAR_KEYWORD for parameter in parameters),
                    "command DTOs must reject unknown keyword fields",
                )

    def test_command_instance_rejects_mutation_and_unknown_fields(self):
        register_ship = contracts.RegisterShip(ship_id="SHIP-1", name="Rescue One")

        with self.assertRaises(FrozenInstanceError):
            register_ship.name = "Changed"
        with self.assertRaises(TypeError):
            contracts.RegisterShip(ship_id="SHIP-1", name="Rescue One", unknown=True)

    def test_result_is_frozen_and_uses_none_for_optional_fields(self):
        result_type = contracts.Result[str]
        result_fields = {field.name: field for field in fields(contracts.Result)}

        self.assertTrue(is_dataclass(contracts.Result))
        self.assertTrue(contracts.Result.__dataclass_params__.frozen)
        self.assertEqual(set(result_fields), {"status", "value", "reason"})
        self.assertIs(result_fields["status"].default, MISSING)
        self.assertIsNone(result_fields["value"].default)
        self.assertIsNone(result_fields["reason"].default)

        result = result_type(status="applied")
        self.assertIsNone(result.value)
        self.assertIsNone(result.reason)

    def test_result_preserves_each_contract_status_and_reason(self):
        for status in RESULT_STATUSES:
            with self.subTest(status=status):
                result = contracts.Result[str](status=status, value="snapshot")
                self.assertEqual(result.status, status)
                self.assertEqual(result.value, "snapshot")
                self.assertIsNone(result.reason)

        for reason in RESULT_REASONS:
            with self.subTest(reason=reason):
                result = contracts.Result[str](status="rejected", reason=reason)
                self.assertEqual(result.status, "rejected")
                self.assertIsNone(result.value)
                self.assertEqual(result.reason, reason)

    def test_result_accepts_each_sequencing_reason(self):
        for reason in SEQUENCING_RESULT_REASONS:
            with self.subTest(reason=reason):
                result = contracts.Result[str](status="rejected", reason=reason)
                self.assertEqual(result.status, "rejected")
                self.assertIsNone(result.value)
                self.assertEqual(result.reason, reason)

    def test_result_rejects_unknown_status_and_reason_values(self):
        with self.assertRaises(ValueError):
            contracts.Result(status="completed")
        with self.assertRaises(ValueError):
            contracts.Result(status="rejected", reason="mystery")


if __name__ == "__main__":
    unittest.main()
