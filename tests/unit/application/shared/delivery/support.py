"""Builders shared by the delivery step tests."""

from rescue.application.contracts import RecordResponse
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission, SeatRequest
from rescue.mission.rules.add_request import add_request
from rescue.state import RunState
from rescue.values import TransitionContext


def response(**overrides):
    fields = {
        "message_id": "message-1",
        "delivery_id": "delivery-1",
        "attempt_number": 1,
        "request_id": "request-1",
        "outcome": "accepted",
        "confirmed_seats": 3,
        "sent_at": "2",
        "received_at": "3",
    }
    return RecordResponse(**(fields | overrides))


def state_with_request(**state_fields):
    mission = add_request(
        Mission("mission-1", "Station A", 10, "0"),
        SeatRequest(
            request_id="request-1",
            command_id="command-1",
            mission_id="mission-1",
            ship_id="ship-1",
            requested_seats=3,
            confirmed_seats=0,
            outcome="pending",
            submitted_at="1",
            revision_id="revision-1",
        ),
        TransitionContext(event_id="created", at="1", reason="test"),
    )
    return RunState("run-1", "central-1", B3Market("market-1"), missions=(mission,), **state_fields)
