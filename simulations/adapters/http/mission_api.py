"""Translate simulation contracts to the public rescue HTTP API without domain imports."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from urllib.parse import quote

import httpx

from simulations.adapters.ports.mission_api import MissionApiABC
from simulations.models.api_state import ApiState
from simulations.models.decision_view import DecisionView
from simulations.models.delivery_view import DeliveryView
from simulations.models.identifier import Identifier
from simulations.models.mission_progress import MissionProgress
from simulations.models.operation_name import OperationName
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.request_view import RequestView
from simulations.models.run_view import RunView
from simulations.models.selected_allocation import SelectedAllocation
from simulations.models.sequence_gap import SequenceGap
from simulations.models.session_view import SessionView


class HttpMissionApi(MissionApiABC):
    """Use an injected open HTTP client, retaining complete wire responses for playback.

    Constructed by CLI or web composition; every action goes through reviewed HTTP routes,
    never through direct application or domain calls. The caller owns an injected client.
    """

    def __init__(self, client):
        """Accept an httpx-compatible client, including an in-process HTTP test transport."""
        self.client = client
        self.calls = []
        self.trace_calls = []
        self.last_raw_state = None
        self.last_outcomes = []

    def raw_invoke(self, run_id, operation, payload):
        """Submit one exact JSON payload and preserve its full response without retrying."""
        response = self.client.post(
            f"/runs/{quote(run_id, safe='')}/operations/{operation}", json=payload
        )
        value = response.json()
        call = {
            "operation": str(operation),
            "input": payload,
            "http_status": response.status_code,
            "result": value,
        }
        self.calls.append(call)
        self.trace_calls.append(call)
        return response.status_code, value

    def create_run(self, namespace, policy):
        """Create a fresh run with its deterministic policy before submitting any actions."""
        payload = {
            "application_run_id": namespace,
            "central_id": f"{namespace}-central",
            "policies": [
                {
                    "policy_id": policy.policy_id,
                    "revision": policy.revision,
                    "name": policy.policy_name,
                    "selection_criteria": policy.selection_criteria,
                }
            ],
        }
        response = self.client.post("/runs", json=payload)
        raw = response.json()
        self.trace_calls.append(
            {
                "operation": "create_run",
                "input": payload,
                "http_status": response.status_code,
                "result": raw,
            }
        )
        return OperationOutcome(
            operation=OperationName.CREATE_RUN,
            http_status=response.status_code,
            application_status="created" if response.is_success else "failed",
            reason=raw.get("detail"),
            value=RunView(run_id=raw["application_run_id"]) if response.is_success else None,
        )

    def invoke(self, run_id, command):
        """Encode one typed command and project the result needed by simulation services."""
        status, raw = self.raw_invoke(run_id, command.operation, _payload(command))
        return self.project(command.operation, status, raw)

    def project(self, operation, status, raw):
        """Convert selected wire values to strict projections while retaining full calls."""
        value = raw.get("value")
        projection = None
        if value and operation is OperationName.MOBILISE:
            projection = DecisionView(
                decision_id=value["decision_id"],
                allocations=tuple(
                    SelectedAllocation(
                        decision_id=value["decision_id"],
                        evaluation_id=item["evaluation_id"],
                        rank=item["rank"],
                        ship_id=item["ship_id"],
                        proposed_seats=item["proposed_seats"],
                        revision_id=item["revision"]["revision_id"],
                    )
                    for item in value["evaluations"]
                    if item["selected"]
                ),
            )
        elif value and operation in {
            OperationName.CREATE_REQUEST,
            OperationName.RECORD_RESPONSE,
            OperationName.CANCEL_REQUEST,
            OperationName.EXPIRE_REQUEST,
        }:
            projection = _request(value)
        identifiers = tuple(
            Identifier(name=key, value=value[key])
            for key in ("request_id", "ship_id", "decision_id")
            if isinstance(value, dict) and isinstance(value.get(key), str)
        )
        return OperationOutcome(
            operation=operation,
            http_status=status,
            application_status=raw.get("status"),
            reason=raw.get("reason") or raw.get("detail"),
            value=projection,
            identifiers=identifiers,
        )

    def progress(self, run_id, mission_id, at):
        """Read authoritative seat accounting at the exact logical time."""
        status, raw = self.raw_invoke(
            run_id, "get_progress", {"mission_id": mission_id, "now": str(at)}
        )
        if status != 200 or not isinstance(raw.get("value"), dict):
            raise ValueError(f"Progress unavailable: {raw}")
        return MissionProgress(mission_id=mission_id, **raw["value"])

    def raw_state(self, run_id):
        """Read and retain the complete committed snapshot for historical viewing."""
        response = self.client.get(f"/runs/{quote(run_id, safe='')}/state")
        response.raise_for_status()
        self.last_raw_state = response.json()
        self.trace_calls.append(
            {
                "operation": "read_state",
                "input": {"run_id": run_id},
                "http_status": response.status_code,
                "result": self.last_raw_state,
            }
        )
        return self.last_raw_state

    def state(self, run_id):
        """Project request and session identities from the complete state response."""
        raw = self.raw_state(run_id)
        sessions = tuple(
            SessionView(
                session_id=item["session_id"],
                version=item["version"],
                ship_id=item["session_id"].removeprefix("local:"),
                direction="inbound",
                next_inbound=item["next_inbound"],
                next_outbound=item["next_outbound"],
                gaps=tuple(
                    SequenceGap(from_sequence=gap["from_sequence"], count=gap["count"])
                    for gap in item["gaps"]
                ),
            )
            for item in raw["session_index"]
        )
        messages = {item[0]["message_id"]: item[0] for item in raw["message_index"]}
        deliveries = tuple(
            DeliveryView(
                delivery_id=item[0],
                message_id=item[1],
                sequence=item[2]["envelope"]["sequence"] if item[2].get("envelope") else 1,
                attempt_number=item[2]["attempt_number"],
                sent_at=Decimal(messages.get(item[1], {}).get("sent_at", "0")),
                received_at=None
                if item[2]["received_at"] is None
                else Decimal(item[2]["received_at"]),
                disposition=item[2]["disposition"],
            )
            for item in raw["delivery_index"]
        )
        return ApiState(
            requests=tuple(
                _request(request) for mission in raw["missions"] for request in mission["requests"]
            ),
            sessions=sessions,
            deliveries=deliveries,
        )

    def invoke_batch(self, run_id, commands):
        """Join at most two competing HTTP submissions without assuming commit order."""
        if not 1 <= len(commands) <= 2:
            raise ValueError("a batch requires one or two commands")
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(self.invoke, run_id, command) for command in commands]
            return tuple(future.result() for future in futures)


def new_http_client(base_url):
    """Construct the CLI transport with finite timeouts, no proxy environment and no retries."""
    return httpx.Client(
        base_url=base_url,
        trust_env=False,
        timeout=httpx.Timeout(connect=2, pool=2, read=10, write=10),
        transport=httpx.HTTPTransport(retries=0),
    )


def _request(value):
    return RequestView(
        request_id=value["request_id"],
        mission_id=value["mission_id"],
        ship_id=value["ship_id"],
        requested_seats=value["requested_seats"],
        confirmed_seats=value["confirmed_seats"],
        status=value["outcome"],
        response_deadline=Decimal(value["response_deadline"]),
    )


def _payload(c):
    if c.operation is OperationName.REGISTER_MISSION:
        body = {
            "mission_id": c.mission_id,
            "station_name": c.mission.station_name,
            "people_count": c.mission.demand,
            "created_at": str(c.at),
        }
    elif c.operation is OperationName.REGISTER_SHIP:
        body = {"ship_id": c.ship_id, "name": c.ship.name}
    elif c.operation is OperationName.PUBLISH_AVAILABILITY:
        body = {
            "availability": {
                "availability_id": c.availability_id,
                "ship_id": c.ship_id,
                "total_seats": c.capacity,
                "arrival_estimate_seconds": str(c.arrival_estimate),
                "available": c.available,
                "recorded_at": str(c.at),
            }
        }
    elif c.operation is OperationName.PUBLISH_OFFER:
        body = {
            "offer_id": c.offer_id,
            "mission_id": c.mission_id,
            "ship_id": c.ship_id,
            "revision": {
                "revision_id": c.revision_id,
                "revision_number": c.revision_number,
                "capacity": c.offer_capacity,
                "arrival_estimate_seconds": str(c.arrival_estimate),
                "available": c.available,
                "recorded_at": str(c.at),
            },
        }
    elif c.operation is OperationName.MOBILISE:
        body = {
            "mission_id": c.mission_id,
            "policy_id": c.policy_id,
            "policy_revision": c.policy_revision,
            "now": str(c.at),
        }
    elif c.operation is OperationName.CREATE_REQUEST:
        body = {
            "command_id": c.command_id,
            "mission_id": c.mission_id,
            "ship_id": c.ship_id,
            "requested_seats": c.requested_seats,
            "revision_id": c.revision_id,
            "now": str(c.at),
            "response_deadline": str(c.response_deadline),
            "decision_id": c.decision_id,
        }
    elif c.operation is OperationName.RECORD_RESPONSE:
        body = {
            "message_id": c.message_id,
            "delivery_id": c.delivery_id,
            "attempt_number": c.attempt_number,
            "request_id": c.request_id,
            "outcome": str(c.outcome),
            "confirmed_seats": c.confirmed_seats,
            "sent_at": str(c.sent_at),
            "received_at": None if c.received_at is None else str(c.received_at),
            "communication_rtt_seconds": None
            if c.communication_rtt_seconds is None
            else str(c.communication_rtt_seconds),
            "envelope": c.envelope.model_dump(mode="json"),
        }
    elif c.operation in {OperationName.CANCEL_REQUEST, OperationName.EXPIRE_REQUEST}:
        body = {"mission_id": c.mission_id, "request_id": c.request_id, "now": str(c.at)}
        if c.operation is OperationName.CANCEL_REQUEST:
            body["reason"] = c.reason
    elif c.operation is OperationName.GET_PROGRESS:
        return {"mission_id": c.mission_id, "now": str(c.at)}
    elif c.operation is OperationName.GET_SESSION:
        return {"session_id": c.session_id}
    elif c.operation is OperationName.GET_DELIVERIES:
        return {"message_id": c.message_id}
    else:
        raise ValueError(f"Unsupported operation {c.operation}")
    return {"command": body}
