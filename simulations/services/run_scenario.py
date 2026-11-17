"""Execute one bounded real-API mission timeline and retain its immutable observations."""

from decimal import Decimal

from simulations.models.close_kind import CloseKind
from simulations.models.close_request import CloseRequest
from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.evidence import Evidence
from simulations.models.observation import Observation
from simulations.models.observe import Observe
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.publish_fleet import PublishFleet
from simulations.models.reply_kind import ReplyKind
from simulations.models.response_outcome import ResponseOutcome
from simulations.models.scenario_result import ScenarioResult
from simulations.models.session_direction import SessionDirection
from simulations.models.session_envelope import SessionEnvelope
from simulations.models.ship_reply import ShipReply
from simulations.models.solver_round import SolverRound
from simulations.services.solver_round import request_command, solver_round


def run_scenario(api, profile, namespace, on_step=None, before_event=None):
    """Run every declared event, notify an injected observer, and evaluate final evidence.

    Called by CLI and web entrypoints. Observation callbacks make transcript retention and
    terminal streaming possible without introducing presentation or concrete I/O here.
    """
    run_id = namespace
    mission_id = f"{namespace}-mission"
    matched = set()
    observations = []
    progress = None
    failure = None
    ship_ids = {ship.ship_key: f"{namespace}-{ship.ship_key}" for ship in profile.ships}
    fleet = {
        ship.ship_key: {
            "capacity": ship.capacity,
            "available": True,
            "revision": 0,
            "arrival": ship.arrival,
        }
        for ship in profile.ships
    }
    sent_messages = {}
    try:
        created = api.create_run(namespace, profile.policy)
        _require(created)
        run_id = created.value.run_id
        _require(
            api.invoke(
                run_id,
                OperationCommand(
                    operation=OperationName.REGISTER_MISSION,
                    mission_id=mission_id,
                    mission=profile.mission,
                    at=Decimal("0"),
                ),
            )
        )
        for ship in profile.ships:
            _require(
                api.invoke(
                    run_id,
                    OperationCommand(
                        operation=OperationName.REGISTER_SHIP,
                        ship_id=ship_ids[ship.ship_key],
                        ship=ship,
                    ),
                )
            )
            _publish(
                api, run_id, mission_id, ship.ship_key, ship_ids, fleet, Decimal("0"), namespace
            )
        progress = api.progress(run_id, mission_id, Decimal("0"))
        if on_step:
            on_step(None, (), progress, ())
        events = sorted(profile.events, key=lambda item: item.order_key)
        if len(events) > profile.event_budget or any(
            event.time > profile.horizon for event in events
        ):
            raise ValueError("Timeline exceeds declared event/time bounds")
        for event in events:
            if before_event:
                before_event(event, run_id, mission_id)
            action = event.action
            prefix = f"{namespace}-{event.ordinal}"
            deadline = (
                Decimal("10")
                if event.time == 0
                else (Decimal("20") if event.time < 20 else Decimal("40"))
            )
            if isinstance(action, PublishFleet):
                outcomes = []
                for update in action.updates:
                    prior = fleet[update.ship_key]
                    if update.capacity is not None:
                        prior["capacity"] = update.capacity
                    if update.available is not None:
                        prior["available"] = update.available
                    outcomes.extend(
                        _publish(
                            api,
                            run_id,
                            mission_id,
                            update.ship_key,
                            ship_ids,
                            fleet,
                            event.time,
                            prefix,
                        )
                    )
                outcomes = tuple(outcomes)
            elif isinstance(action, SolverRound):
                if progress.status == "complete":
                    raise ValueError("Cannot mobilise a completed mission")
                outcomes = solver_round(
                    api,
                    run_id,
                    mission_id,
                    profile.policy,
                    event.time,
                    action.response_deadline,
                    prefix,
                    submit=action.submit,
                )
            elif isinstance(action, ConcurrentRequests):
                proposal = solver_round(
                    api,
                    run_id,
                    mission_id,
                    profile.policy,
                    event.time,
                    deadline,
                    prefix,
                    submit=False,
                )[0]
                selected = proposal.value.allocations
                target = action.allocation or next(
                    item for item in selected if item.ship_id == ship_ids[action.ship_key]
                )
                commands = tuple(
                    request_command(
                        target, mission_id, event.time, deadline, f"{prefix}-compete-{slot}"
                    )
                    for slot in range(action.count)
                )
                outcomes = (proposal, *api.invoke_batch(run_id, commands))
                for allocation in selected:
                    if allocation.ship_id != target.ship_id:
                        outcomes += (
                            api.invoke(
                                run_id,
                                request_command(
                                    allocation,
                                    mission_id,
                                    event.time,
                                    deadline,
                                    f"{prefix}-other-{allocation.rank}",
                                ),
                            ),
                        )
            elif isinstance(action, ShipReply):
                state = api.state(run_id)
                requests = [
                    request
                    for request in state.requests
                    if request.ship_id == ship_ids[action.request.ship_key]
                ]
                if action.request.occurrence > len(requests):
                    raise ValueError(f"Request not submitted: {action.request}")
                request = requests[action.request.occurrence - 1]
                if action.replay_of in sent_messages:
                    previous = sent_messages[action.replay_of]
                    command = previous.model_copy(
                        update={
                            "delivery_id": f"{prefix}-delivery",
                            "attempt_number": action.delivery_attempt,
                            "received_at": event.time,
                        }
                    )
                else:
                    session_id = f"local:{request.ship_id}"
                    session = next(
                        (item for item in state.sessions if item.session_id == session_id), None
                    )
                    sequence = action.sequence or (session.next_inbound if session else 1)
                    outcome = {
                        ReplyKind.CONFIRM: ResponseOutcome.ACCEPTED,
                        ReplyKind.PARTIAL: ResponseOutcome.PARTIALLY_ACCEPTED,
                        ReplyKind.REFUSE: ResponseOutcome.REFUSED,
                    }[action.reply]
                    command = OperationCommand(
                        operation=OperationName.RECORD_RESPONSE,
                        request_id=request.request_id,
                        message_id=f"{namespace}-{action.replay_of or action.message_label}",
                        delivery_id=f"{prefix}-delivery",
                        attempt_number=action.delivery_attempt,
                        outcome=outcome,
                        confirmed_seats=action.seats or 0,
                        sent_at=event.time if action.sent_at is None else action.sent_at,
                        received_at=event.time,
                        envelope=SessionEnvelope(
                            session_id=session_id,
                            version=session.version if session else 1,
                            direction=SessionDirection.INBOUND,
                            sequence=sequence,
                        ),
                    )
                    sent_messages[action.message_label] = command
                outcomes = (api.invoke(run_id, command),)
            elif isinstance(action, CloseRequest):
                state = api.state(run_id)
                requests = [
                    request
                    for request in state.requests
                    if request.ship_id == ship_ids[action.request.ship_key]
                ]
                request = requests[action.request.occurrence - 1]
                operation = (
                    OperationName.CANCEL_REQUEST
                    if action.close_as is CloseKind.CANCEL
                    else OperationName.EXPIRE_REQUEST
                )
                outcomes = (
                    api.invoke(
                        run_id,
                        OperationCommand(
                            operation=operation,
                            mission_id=mission_id,
                            request_id=request.request_id,
                            at=event.time,
                            reason="scripted cancellation"
                            if action.close_as is CloseKind.CANCEL
                            else None,
                        ),
                    ),
                )
            elif isinstance(action, Observe):
                outcomes = (
                    OperationOutcome(
                        operation=OperationName.GET_PROGRESS,
                        http_status=200,
                        application_status="observed",
                    ),
                )
            else:
                raise ValueError(f"Unsupported action {action}")
            for outcome in outcomes:
                if not 200 <= outcome.http_status < 300:
                    raise ValueError(f"HTTP failure: {outcome.reason}")
            progress = api.progress(run_id, mission_id, event.time)
            evidence = _evidence(profile, event, outcomes, progress, api, run_id)
            matched.update(item.situation_id for item in evidence if item.matched)
            observations.append(
                Observation(
                    ordinal=len(observations),
                    logical_time=event.time,
                    event_or_batch_id=event.event_id,
                    outcome=outcomes[-1],
                    progress=progress,
                    evidence=evidence,
                )
            )
            if on_step:
                on_step(event, outcomes, progress, evidence)
        expected = profile.expectation
        if progress.status != expected.mission_status or (
            progress.confirmed,
            progress.pending,
            progress.unconfirmed,
        ) != (expected.confirmed, expected.pending, expected.unconfirmed):
            failure = "Final mission progress did not match declared expectation"
        missing = tuple(item for item in profile.included_situations if item not in matched)
        if not failure and missing:
            failure = "Missing situation evidence: " + ", ".join(item.value for item in missing)
        required_missing = tuple(
            item for item in expected.required_situations if item not in matched
        )
        if not failure and required_missing:
            failure = "Missing required situation evidence"
    except Exception as error:
        failure = str(error) or type(error).__name__
    return ScenarioResult(
        profile_id=profile.scenario_id,
        run_id=run_id,
        mission_id=mission_id,
        passed=failure is None,
        matched_situations=tuple(item for item in profile.included_situations if item in matched),
        missing_situations=tuple(
            item for item in profile.included_situations if item not in matched
        ),
        last_progress=progress,
        failure_detail=failure,
        observations=tuple(observations),
    )


def _require(outcome):
    if not 200 <= outcome.http_status < 300 or outcome.application_status in {"rejected", "failed"}:
        raise ValueError(f"Setup failed: {outcome.reason}")


def _publish(api, run_id, mission_id, key, ship_ids, fleet, now, prefix):
    value = fleet[key]
    value["revision"] += 1
    ship_id = ship_ids[key]
    common = {
        "ship_id": ship_id,
        "arrival_estimate": value["arrival"],
        "available": value["available"],
        "at": now,
    }
    availability = api.invoke(
        run_id,
        OperationCommand(
            operation=OperationName.PUBLISH_AVAILABILITY,
            availability_id=f"{prefix}-{key}-availability-{value['revision']}",
            capacity=value["capacity"],
            **common,
        ),
    )
    offer = api.invoke(
        run_id,
        OperationCommand(
            operation=OperationName.PUBLISH_OFFER,
            mission_id=mission_id,
            offer_id=f"{run_id}-{key}-offer",
            revision_id=f"{run_id}-{key}-revision-{value['revision']}",
            revision_number=value["revision"],
            offer_capacity=value["capacity"],
            **common,
        ),
    )
    _require(availability)
    _require(offer)
    return availability, offer


def _evidence(profile, event, outcomes, progress, api, run_id):
    evidence = []
    for situation in event.situation_ids:
        recipe = next(item for item in profile.recipes if item.situation_id == situation)
        name = recipe.evidence.check_name
        expected = recipe.evidence.expected
        last = outcomes[-1]
        if name == "application_status":
            actual = last.application_status or ""
        elif name in {"reason", "delivery_reason"}:
            actual = last.reason or ""
        elif name == "partial_and_refusal":
            statuses = tuple(item.status for item in api.state(run_id).requests)
            actual = (
                "partially_accepted" in statuses
                and "refused" in statuses
                and progress.confirmed == 6
                and progress.pending == 0
            )
        elif name == "shortfall":
            actual = progress.additional_needed if not outcomes[0].value.allocations else -1
        elif name == "session_gap_and_obsolete_sequence":
            state = api.state(run_id)
            actual = (
                "gap" if any(session.gaps for session in state.sessions) else "no_gap",
                last.reason or "",
            )
        elif name == "message_replay":
            state = api.state(run_id)
            repeated = any(
                sum(other.message_id == item.message_id for other in state.deliveries) > 1
                and item.attempt_number > 1
                for item in state.deliveries
            )
            actual = (
                repeated
                and last.application_status == "ignored"
                and progress.confirmed == profile.mission.demand
            )
        elif name == "concurrent_outcomes":
            statuses = [item.application_status for item in outcomes[1:3]]
            reasons = [item.reason for item in outcomes[1:3]]
            actual = (
                ("applied", "insufficient_capacity")
                if statuses.count("applied") == 1 and "insufficient_capacity" in reasons
                else tuple(str(item) for item in statuses)
            )
        else:
            actual = getattr(progress, name, "unavailable")
        evidence.append(
            Evidence(
                situation_id=situation,
                triggering_event_ids=(event.event_id,),
                check_name=name,
                expected=expected,
                observed=actual,
                matched=actual == expected,
            )
        )
    return tuple(evidence)
