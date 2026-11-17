"""Execute one bounded mission timeline through an injected API port."""

from decimal import Decimal
from typing import TypeAlias

from simulations.adapters.ports.mission_api import MissionApiABC
from simulations.models.close_kind import CloseKind
from simulations.models.close_request import CloseRequest
from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.evidence import Evidence
from simulations.models.fleet_update import FleetUpdate
from simulations.models.mission_progress import MissionProgress
from simulations.models.observation import Observation
from simulations.models.observe import Observe
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.publish_fleet import PublishFleet
from simulations.models.run_view import RunView
from simulations.models.scenario_profile import ScenarioProfile
from simulations.models.scenario_result import ScenarioResult
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.solver_round import SolverRound
from simulations.models.timeline_event import TimelineEvent
from simulations.services.solver_round import solver_round

Scalar: TypeAlias = str | int | bool | Decimal | tuple[str | int | bool | Decimal, ...]


def run_scenario(
    api: MissionApiABC,
    profile: ScenarioProfile,
    namespace: str,
) -> ScenarioResult:
    """Create a fresh one-mission run, execute every declared event, and compare outcomes."""
    mission_id = f"{namespace}-mission"
    ship_ids = {ship.ship_key: f"{namespace}-{ship.ship_key}" for ship in profile.ships}
    run_id = namespace
    matched: set[SituationId] = set()
    progress: MissionProgress | None = None

    try:
        created = api.create_run(namespace)
        run_view = created.value
        if not 200 <= created.http_status < 300 or not isinstance(run_view, RunView):
            raise ScenarioExecutionError(_failure_text(created, "create_run did not return a run"))
        run_id = run_view.run_id

        _invoke_or_fail(
            api,
            run_id,
            OperationCommand(
                operation=OperationName.REGISTER_MISSION,
                command_id=f"{namespace}-register-mission",
                mission_id=mission_id,
                mission=profile.mission,
                at=Decimal("0"),
            ),
        )
        for ship in profile.ships:
            ship_id = ship_ids[ship.ship_key]
            _invoke_or_fail(
                api,
                run_id,
                OperationCommand(
                    operation=OperationName.REGISTER_SHIP,
                    command_id=f"{namespace}-register-{ship.ship_key}",
                    ship=ship,
                    at=Decimal("0"),
                ),
            )
            initial = FleetUpdate(
                ship_key=ship_id,
                capacity=ship.capacity,
                available=True,
                offer_revision=ship.offer_revision,
            )
            self_setup = PublishFleet(updates=(initial,))
            _publish_fleet(
                api,
                run_id,
                self_setup,
                ship_ids,
                namespace,
                Decimal("0"),
                ship_by_key={ship.ship_key: ship},
            )

        progress = api.progress(run_id, mission_id)
        observations: list[Observation] = []
        ordered_events = sorted(profile.events, key=lambda event: event.order_key)
        if len(ordered_events) > profile.event_budget:
            raise ScenarioExecutionError("event count exceeds the configured budget")
        if any(event.time > profile.horizon for event in ordered_events):
            raise ScenarioExecutionError("event time exceeds the configured horizon")

        request_bindings: dict[tuple[str, int], str] = {}
        request_occurrences: dict[str, int] = {}
        next_ordinal = 0

        for event in ordered_events:
            outcomes = _execute_event(
                api,
                run_id,
                mission_id,
                namespace,
                profile,
                event,
                ship_ids,
                request_bindings,
                request_occurrences,
            )
            progress = api.progress(run_id, mission_id)
            evidence = _evidence_for_event(profile, event, outcomes, progress, api, run_id)
            matched.update(item.situation_id for item in evidence if item.matched)
            observations.append(
                Observation(
                    ordinal=next_ordinal,
                    logical_time=event.time,
                    event_or_batch_id=event.event_id,
                    outcome=outcomes[-1],
                    progress=progress,
                    evidence=evidence,
                )
            )
            next_ordinal += 1

        missing = tuple(
            situation for situation in profile.included_situations if situation not in matched
        )
        expectation = profile.expectation
        final_matches = progress is not None and (
            progress.status == expectation.mission_status
            and progress.confirmed == expectation.confirmed
            and progress.pending == expectation.pending
            and progress.unconfirmed == expectation.unconfirmed
        )
        missing_required = tuple(
            situation for situation in expectation.required_situations if situation not in matched
        )
        passed = final_matches and not missing and not missing_required
        failure = None
        if not final_matches:
            failure = "final mission progress did not match the declared expectation"
        elif missing:
            failure = f"missing situation evidence: {', '.join(item.value for item in missing)}"
        elif missing_required:
            failure = (
                f"missing required evidence: {', '.join(item.value for item in missing_required)}"
            )
        return ScenarioResult(
            profile_id=profile.scenario_id,
            run_id=run_id,
            mission_id=mission_id,
            passed=passed,
            matched_situations=tuple(
                situation for situation in profile.included_situations if situation in matched
            ),
            missing_situations=missing,
            last_progress=progress,
            failure_detail=failure,
        )
    except Exception as error:  # An operational failure becomes an explicit failed scenario.
        missing = tuple(
            situation for situation in profile.included_situations if situation not in matched
        )
        return ScenarioResult(
            profile_id=profile.scenario_id,
            run_id=run_id,
            mission_id=mission_id,
            passed=False,
            matched_situations=tuple(
                situation for situation in profile.included_situations if situation in matched
            ),
            missing_situations=missing,
            last_progress=progress,
            failure_detail=str(error) or type(error).__name__,
        )


class ScenarioExecutionError(RuntimeError):
    """Represent an API, binding, bound, or expectation failure in a scenario."""


def _invoke_or_fail(api: MissionApiABC, run_id: str, command: OperationCommand) -> OperationOutcome:
    outcome = api.invoke(run_id, command)
    if not 200 <= outcome.http_status < 300:
        raise ScenarioExecutionError(_failure_text(outcome, f"{command.operation} failed"))
    return outcome


def _failure_text(outcome: OperationOutcome, fallback: str) -> str:
    return outcome.reason or outcome.application_status or f"{fallback}: HTTP {outcome.http_status}"


def _publish_fleet(
    api: MissionApiABC,
    run_id: str,
    action: PublishFleet,
    ship_ids: dict[str, str],
    namespace: str,
    at: Decimal,
    *,
    ship_by_key: dict[str, object] | None = None,
) -> tuple[OperationOutcome, ...]:
    outcomes: list[OperationOutcome] = []
    for index, update in enumerate(action.updates):
        ship_id = ship_ids.get(update.ship_key, update.ship_key)
        if update.capacity is not None or update.available is not None:
            outcomes.append(
                _invoke_or_fail(
                    api,
                    run_id,
                    OperationCommand(
                        operation=OperationName.PUBLISH_AVAILABILITY,
                        command_id=f"{namespace}-availability-{index}-{at}",
                        fleet_update=update.model_copy(update={"ship_key": ship_id}),
                        at=at,
                    ),
                )
            )
        if update.capacity is not None or update.offer_revision is not None:
            ship = (ship_by_key or {}).get(update.ship_key)
            outcomes.append(
                _invoke_or_fail(
                    api,
                    run_id,
                    OperationCommand(
                        operation=OperationName.PUBLISH_OFFER,
                        command_id=f"{namespace}-offer-{index}-{at}",
                        ship=ship,
                        fleet_update=update.model_copy(update={"ship_key": ship_id}),
                        at=at,
                    ),
                )
            )
    return tuple(outcomes)


def _execute_event(
    api: MissionApiABC,
    run_id: str,
    mission_id: str,
    namespace: str,
    profile: ScenarioProfile,
    event: TimelineEvent,
    ship_ids: dict[str, str],
    request_bindings: dict[tuple[str, int], str],
    request_occurrences: dict[str, int],
) -> tuple[OperationOutcome, ...]:
    action = event.action
    prefix = f"{namespace}-{event.ordinal}-{event.event_id}"
    if isinstance(action, PublishFleet):
        return _publish_fleet(api, run_id, action, ship_ids, prefix, event.time)
    if isinstance(action, SolverRound):
        submitted = solver_round(
            api,
            run_id,
            mission_id,
            profile.policy,
            event.time,
            _response_deadline(profile, event),
            prefix,
            submit=action.submit,
        )
        for outcome in submitted[1:]:
            allocation = _allocation_for_outcome(outcome, submitted[0])
            ship_key = _ship_key_for_allocation(profile, allocation, ship_ids)
            if ship_key is not None:
                request_occurrences[ship_key] = request_occurrences.get(ship_key, 0) + 1
                request_id = _request_id(outcome)
                if request_id:
                    request_bindings[(ship_key, request_occurrences[ship_key])] = request_id
        return submitted
    if isinstance(action, ShipReply):
        selector = action.request
        request_id = _resolve_request(api, run_id, selector.ship_key, selector.occurrence, ship_ids)
        state = api.state(run_id)
        ship_id = ship_ids[selector.ship_key]
        session = next(
            (
                item
                for item in state.sessions
                if item.ship_id == ship_id and item.direction == "inbound"
            ),
            None,
        )
        if session is None:
            raise ScenarioExecutionError(f"inbound session not found for {selector.ship_key}")
        sequence = session.last_sequence + 1
        message_id = action.replay_of or f"{namespace}-message-{action.message_label}"
        return (
            api.invoke(
                run_id,
                OperationCommand(
                    operation=OperationName.RECORD_RESPONSE,
                    command_id=f"{prefix}-delivery-{action.delivery_attempt}",
                    request_id=request_id,
                    reply=action.reply,
                    seats=action.seats,
                    message_id=message_id,
                    session_id=session.session_id,
                    sequence=sequence,
                    attempt_number=action.delivery_attempt,
                    at=event.time,
                ),
            ),
        )
    if isinstance(action, CloseRequest):
        request_id = _resolve_request(
            api, run_id, action.request.ship_key, action.request.occurrence, ship_ids
        )
        operation = (
            OperationName.CANCEL_REQUEST
            if action.close_as is CloseKind.CANCEL
            else OperationName.EXPIRE_REQUEST
        )
        return (
            api.invoke(
                run_id,
                OperationCommand(
                    operation=operation,
                    command_id=prefix,
                    request_id=request_id,
                    at=event.time,
                ),
            ),
        )
    if isinstance(action, ConcurrentRequests):
        commands = tuple(
            OperationCommand(
                operation=OperationName.CREATE_REQUEST,
                command_id=f"{prefix}-slot-{slot}",
                mission_id=mission_id,
                allocation=action.allocation,
                requested_seats=action.allocation.proposed_seats,
                response_deadline=_response_deadline(profile, event),
                at=event.time,
            )
            for slot in range(action.count)
        )
        outcomes = api.invoke_batch(run_id, commands)
        if len(outcomes) != action.count:
            raise ScenarioExecutionError(
                "concurrent API batch returned the wrong number of outcomes"
            )
        return outcomes
    if isinstance(action, Observe):
        outcome = OperationOutcome(
            operation=OperationName.GET_PROGRESS,
            http_status=200,
            application_status="observed",
        )
        api.progress(run_id, mission_id)
        return (outcome,)
    raise ScenarioExecutionError(f"unsupported timeline action: {type(action).__name__}")


def _response_deadline(profile: ScenarioProfile, event: TimelineEvent) -> Decimal:
    """Use a bounded default deadline when a solver action has no explicit override."""
    return min(event.time + Decimal("10"), profile.horizon)


def _resolve_request(
    api: MissionApiABC,
    run_id: str,
    ship_key: str,
    occurrence: int,
    ship_ids: dict[str, str],
) -> str:
    state = api.state(run_id)
    requests = tuple(item for item in state.requests if item.ship_id == ship_ids[ship_key])
    if occurrence > len(requests):
        raise ScenarioExecutionError(
            f"request selector {ship_key}#{occurrence} has no actual request binding"
        )
    return requests[occurrence - 1].request_id


def _request_id(outcome: OperationOutcome) -> str | None:
    if hasattr(outcome.value, "request_id"):
        return outcome.value.request_id
    for identifier in outcome.identifiers:
        if identifier.name == "request_id":
            return identifier.value
    return None


def _allocation_for_outcome(outcome: OperationOutcome, proposal: OperationOutcome):
    value = proposal.value
    allocations = getattr(value, "allocations", ())
    for allocation in allocations:
        if allocation.ship_id in {
            item.value for item in outcome.identifiers if item.name == "ship_id"
        }:
            return allocation
    return None


def _ship_key_for_allocation(
    profile: ScenarioProfile, allocation: object, ship_ids: dict[str, str]
) -> str | None:
    if allocation is None:
        return None
    return next(
        (ship.ship_key for ship in profile.ships if ship_ids[ship.ship_key] == allocation.ship_id),
        None,
    )


def _evidence_for_event(
    profile: ScenarioProfile,
    event: TimelineEvent,
    outcomes: tuple[OperationOutcome, ...],
    progress: MissionProgress,
    api: MissionApiABC,
    run_id: str,
) -> tuple[Evidence, ...]:
    results: list[Evidence] = []
    for recipe in profile.recipes:
        if recipe.situation_id not in profile.included_situations or recipe.action != event.action:
            continue
        observed = _projection(recipe.evidence.check_name, outcomes, progress, api, run_id)
        expected: Scalar = recipe.evidence.expected  # validated by EvidencePredicate
        results.append(
            Evidence(
                situation_id=recipe.situation_id,
                triggering_event_ids=(event.event_id,),
                check_name=recipe.evidence.check_name,
                expected=expected,
                observed=observed,
                matched=observed == expected,
            )
        )
    return tuple(results)


def _projection(
    check_name: str,
    outcomes: tuple[OperationOutcome, ...],
    progress: MissionProgress,
    api: MissionApiABC,
    run_id: str,
) -> Scalar:
    outcome = outcomes[-1]
    if check_name == "http_status":
        return outcome.http_status
    if check_name == "application_status":
        return outcome.application_status or ""
    if check_name == "reason":
        return outcome.reason or ""
    if hasattr(progress, check_name):
        value = getattr(progress, check_name)
        if isinstance(value, (str, int, bool, Decimal)):
            return value
    state = api.state(run_id)
    if check_name.startswith("request."):
        attribute = check_name.removeprefix("request.")
        for request in state.requests:
            value = getattr(request, attribute, None)
            if isinstance(value, (str, int, bool, Decimal)):
                return value
    if check_name.startswith("delivery."):
        attribute = check_name.removeprefix("delivery.")
        for delivery in state.deliveries:
            value = getattr(delivery, attribute, None)
            if isinstance(value, (str, int, bool, Decimal)):
                return value
    if check_name.startswith("session."):
        attribute = check_name.removeprefix("session.")
        for session in state.sessions:
            value = getattr(session, attribute, None)
            if isinstance(value, (str, int, bool, Decimal)):
                return value
    return outcome.application_status or outcome.reason or ""
