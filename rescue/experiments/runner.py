"""Deterministic isolated scenario execution over a fresh central context."""

from __future__ import annotations

import random
from dataclasses import dataclass, fields, is_dataclass, replace
from decimal import Decimal

from rescue.application.contracts import (
    CreateRequest,
    ExpireRequest,
    Mobilise,
    PublishAvailability,
    RecordResponse,
)
from rescue.bootstrap import new_run
from rescue.experiments.models import (
    RescueScenario,
    RunBaseline,
    RunSnapshot,
    ScriptedResponse,
    SimulationRun,
)
from rescue.experiments.results import summarize
from rescue.experiments.timeline import Timeline, TimelineEvent
from rescue.mission.models import Mission, RequestOutcome
from rescue.mission.rules import progress
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import DomainValidationError, normalize_id


@dataclass(frozen=True, slots=True)
class _ResponsePayload:
    message_id: str
    mission_id: str
    request_id: str
    outcome: str
    confirmed_seats: int
    attempt_number: int
    sent_at: Decimal
    received_at: Decimal | None
    communication_rtt_seconds: Decimal | None


def _copy_command_index(entries: tuple[object, ...], run_id: str) -> tuple[object, ...]:
    remapped = []
    for entry in entries:
        if isinstance(entry, tuple) and len(entry) == 5:
            remapped.append((run_id, *entry[1:]))
        else:
            remapped.append(entry)
    return tuple(remapped)


def _baseline_identity_ids(baseline: RunBaseline) -> tuple[str, ...]:
    """Collect typed identities and raw keys carried by baseline indexes."""
    identities: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, tuple):
            for item in value:
                collect(item)
        elif is_dataclass(value):
            for field in fields(value):
                item = getattr(value, field.name)
                if field.name.endswith("_id") and isinstance(item, str):
                    identities.add(item)
                collect(item)

    collect(baseline)
    for entry in baseline.command_index:
        if isinstance(entry, tuple) and len(entry) == 5 and isinstance(entry[1], str):
            identities.add(entry[1])
    for entry in baseline.delivery_index:
        if isinstance(entry, tuple) and len(entry) == 3:
            identities.update(value for value in entry[:2] if isinstance(value, str))
    return tuple(sorted(identities))


def _scripted_response(
    rule: ScriptedResponse,
    request_seats: int,
    rng: random.Random,
) -> tuple[str, int]:
    if rule.outcome == RequestOutcome.REFUSED:
        return RequestOutcome.REFUSED, 0
    specified = rule.confirmed_seats
    if specified is None:
        if rule.outcome == RequestOutcome.ACCEPTED:
            return RequestOutcome.ACCEPTED, request_seats
        if request_seats <= 1:
            return RequestOutcome.REFUSED, 0
        return RequestOutcome.PARTIALLY_ACCEPTED, rng.randint(1, request_seats - 1)
    confirmed = min(specified, request_seats)
    if confirmed <= 0:
        return RequestOutcome.REFUSED, 0
    if confirmed == request_seats:
        return RequestOutcome.ACCEPTED, request_seats
    return RequestOutcome.PARTIALLY_ACCEPTED, confirmed


def simulate(
    scenario: RescueScenario,
    policy: MobilisationPolicy,
    run_id: str,
) -> RunSnapshot:
    """Run a finite scenario from immutable values without touching its source baseline."""
    if not isinstance(scenario, RescueScenario):
        raise DomainValidationError("simulate requires a RescueScenario")
    if not isinstance(policy, MobilisationPolicy):
        raise DomainValidationError("simulate requires a MobilisationPolicy")
    normalized_run_id = normalize_id(run_id)
    baseline = scenario.baseline
    if not baseline.missions:
        raise DomainValidationError("simulation baseline requires at least one mission")

    started_at = max(Decimal("0"), *(mission.created_at for mission in baseline.missions))
    horizon = started_at + scenario.time_horizon_seconds
    context = new_run(
        normalized_run_id,
        f"{normalized_run_id}-central",
        policies=(policy,),
        scenarios=(scenario,),
        reserved_ids=_baseline_identity_ids(baseline),
    )

    def install_baseline(state):
        return (
            replace(
                state,
                market=replace(
                    baseline.market,
                    market_id=f"{normalized_run_id}-market",
                ),
                missions=baseline.missions,
                command_index=_copy_command_index(baseline.command_index, normalized_run_id),
                message_index=baseline.message_index,
                delivery_index=baseline.delivery_index,
                decision_index=baseline.decision_index,
                session_index=baseline.session_index,
            ),
            None,
        )

    context.store.transact(install_baseline)
    timeline = Timeline(horizon=horizon, event_budget=scenario.event_budget)
    rng = random.Random(scenario.seed)
    scenario_sequence = 0

    def next_sequence() -> int:
        nonlocal scenario_sequence
        scenario_sequence += 1
        return scenario_sequence

    for mission in baseline.missions:
        timeline.schedule(
            TimelineEvent(
                instant=started_at,
                kind="mobilise",
                scenario_sequence=next_sequence(),
                payload=mission.mission_id,
            )
        )

    for availability in scenario.availability_changes:
        scheduled_at = started_at + availability.recorded_at
        timeline.schedule(
            TimelineEvent(
                instant=scheduled_at,
                kind="availability",
                scenario_sequence=next_sequence(),
                payload=replace(availability, recorded_at=scheduled_at),
            )
        )

    response_rules = {
        (rule.ship_id, rule.request_ordinal): rule for rule in scenario.response_rules
    }
    profiles = {profile.ship_id: profile for profile in scenario.communication_profiles}
    ship_request_ordinals: dict[str, int] = {}
    for mission in baseline.missions:
        for request in mission.requests:
            ship_request_ordinals[request.ship_id] = (
                ship_request_ordinals.get(request.ship_id, 0) + 1
            )
            if request.outcome != RequestOutcome.PENDING:
                continue
            if request.response_deadline is not None:
                timeline.schedule(
                    TimelineEvent(
                        instant=max(started_at, request.response_deadline),
                        kind="expire",
                        scenario_sequence=next_sequence(),
                        payload=(mission.mission_id, request.request_id),
                    )
                )
            rule = response_rules.get((request.ship_id, ship_request_ordinals[request.ship_id]))
            if rule is not None:
                ordinal = ship_request_ordinals[request.ship_id]
                _schedule_response(
                    timeline,
                    rule,
                    mission,
                    request,
                    ordinal,
                    profiles.get(request.ship_id),
                    rng,
                    next_sequence,
                    context.id_source.next_id("message"),
                )

    run_status = "horizon_reached"
    finished_at = horizon
    current_time = started_at

    def current_missions() -> tuple[Mission, ...]:
        return context.store.snapshot().missions

    def schedule_request_events(mission_id: str, request) -> None:
        if request.response_deadline is not None:
            timeline.schedule(
                TimelineEvent(
                    instant=request.response_deadline,
                    kind="expire",
                    scenario_sequence=next_sequence(),
                    payload=(mission_id, request.request_id),
                )
            )
        ship_request_ordinals[request.ship_id] = ship_request_ordinals.get(request.ship_id, 0) + 1
        rule = response_rules.get((request.ship_id, ship_request_ordinals[request.ship_id]))
        if rule is not None:
            mission = next(item for item in current_missions() if item.mission_id == mission_id)
            _schedule_response(
                timeline,
                rule,
                mission,
                request,
                ship_request_ordinals[request.ship_id],
                profiles.get(request.ship_id),
                rng,
                next_sequence,
                context.id_source.next_id("message"),
            )

    def mobilise_mission(mission_id: str, now: Decimal) -> None:
        mission = next(item for item in current_missions() if item.mission_id == mission_id)
        if progress(mission).additional_needed == 0:
            return
        selection = context.central.mobilise(
            Mobilise(
                mission_id=mission_id,
                policy_id=policy.policy_id,
                policy_revision=policy.revision,
                now=now,
            )
        )
        if selection.status != "applied":
            raise DomainValidationError(f"scenario mobilisation failed: {selection.reason}")
        for evaluation in selection.value.selected:
            created = context.central.create_request(
                CreateRequest(
                    command_id=context.id_source.next_id("command"),
                    mission_id=mission_id,
                    ship_id=evaluation.ship_id,
                    requested_seats=evaluation.proposed_seats,
                    revision_id=evaluation.revision.revision_id,
                    decision_id=selection.value.decision_id,
                    now=now,
                )
            )
            if created.status == "applied":
                schedule_request_events(mission_id, created.value)

    while (event := timeline.pop_next()) is not None:
        current_time = event.instant
        if event.kind == "mobilise":
            mobilise_mission(event.payload, current_time)
        elif event.kind == "availability":
            publication = context.central.publish_availability(
                PublishAvailability(availability=event.payload)
            )
            if publication.status not in {"applied", "replayed"}:
                raise DomainValidationError(
                    f"scenario availability change failed: {publication.reason}"
                )
        elif event.kind == "expire":
            mission_id, request_id = event.payload
            expired = context.central.expire_request(
                ExpireRequest(
                    mission_id=mission_id,
                    request_id=request_id,
                    now=current_time,
                )
            )
            if expired.status == "applied":
                timeline.schedule(
                    TimelineEvent(
                        instant=current_time,
                        kind="mobilise",
                        scenario_sequence=next_sequence(),
                        payload=mission_id,
                    )
                )
        elif event.kind == "response":
            payload = event.payload
            response = context.central.record_response(
                RecordResponse(
                    message_id=payload.message_id,
                    delivery_id=context.id_source.next_id("delivery"),
                    attempt_number=payload.attempt_number,
                    request_id=payload.request_id,
                    outcome=payload.outcome,
                    confirmed_seats=payload.confirmed_seats,
                    sent_at=payload.sent_at,
                    received_at=payload.received_at,
                    communication_rtt_seconds=payload.communication_rtt_seconds,
                )
            )
            if (
                payload.received_at is not None
                and payload.attempt_number == 1
                and response.status == "applied"
            ):
                timeline.schedule(
                    TimelineEvent(
                        instant=current_time,
                        kind="mobilise",
                        scenario_sequence=next_sequence(),
                        payload=payload.mission_id,
                    )
                )
        else:
            raise DomainValidationError(f"unknown scenario event kind: {event.kind!r}")

        missions = current_missions()
        completed = all(progress(mission).confirmed == mission.people_count for mission in missions)
        next_event = timeline.peek_next()
        if completed and (next_event is None or next_event.instant > current_time):
            run_status = "completed"
            finished_at = current_time
            break

    final_state = context.store.snapshot()
    provisional_run = SimulationRun(
        run_id=normalized_run_id,
        scenario_id=scenario.scenario_id,
        scenario_revision=scenario.revision,
        policy_id=policy.policy_id,
        policy_revision=policy.revision,
        started_at=started_at,
        finished_at=finished_at,
        status=run_status,
        result=None,
    )
    provisional_snapshot = RunSnapshot(
        run=provisional_run,
        missions=final_state.missions,
        market=final_state.market,
        command_index=final_state.command_index,
        message_index=final_state.message_index,
        delivery_index=final_state.delivery_index,
        decision_index=final_state.decision_index,
        session_index=final_state.session_index,
    )
    result = summarize(provisional_snapshot)
    finalized_run = replace(provisional_run, result=result)
    return replace(provisional_snapshot, run=finalized_run)


def _schedule_response(
    timeline: Timeline,
    rule: ScriptedResponse,
    mission: Mission,
    request,
    request_ordinal: int,
    profile,
    rng: random.Random,
    next_sequence,
    message_id: str,
) -> None:
    outbound = Decimal("0") if profile is None else profile.outbound_delay_seconds
    decision = Decimal("0") if profile is None else profile.decision_delay_seconds
    returning = Decimal("0") if profile is None else profile.return_delay_seconds
    outcome, confirmed = _scripted_response(rule, request.requested_seats, rng)
    sent_at = request.submitted_at + outbound + decision
    expected_receipt = sent_at + returning
    lost = profile is not None and request_ordinal in profile.loss_rule
    duplicated = profile is not None and request_ordinal in profile.duplication_rule and not lost
    delivery_priority = (
        2 if profile is not None and request_ordinal in profile.reordering_rule else 1
    )

    def payload(attempt_number: int) -> _ResponsePayload:
        return _ResponsePayload(
            message_id=message_id,
            mission_id=mission.mission_id,
            request_id=request.request_id,
            outcome=outcome.value,
            confirmed_seats=confirmed,
            attempt_number=attempt_number,
            sent_at=sent_at,
            received_at=None if lost else expected_receipt,
            communication_rtt_seconds=(None if lost else outbound + returning),
        )

    timeline.schedule(
        TimelineEvent(
            instant=expected_receipt,
            kind="response",
            scenario_sequence=next_sequence(),
            payload=payload(1),
            priority=delivery_priority,
        )
    )
    if duplicated:
        timeline.schedule(
            TimelineEvent(
                instant=expected_receipt,
                kind="response",
                scenario_sequence=next_sequence(),
                payload=payload(2),
                priority=delivery_priority,
            )
        )
