"""Run one finite scenario under one mobilisation policy in a fresh run.

What: the public simulate entry point. It validates its inputs, opens a run through the injected
  factory, installs the baseline, schedules the initial events, plays the timeline until the run
  completes or reaches the horizon, and returns the finished snapshot.
When called: by the application's compare service, the demo and the simulation tests, once per
  scenario and policy.
Why: one entry point keeps the run lifecycle in one place while each step stays in its own file.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

import itertools
import random
from decimal import Decimal

from rescue.experiments.models import RescueScenario, RunSnapshot
from rescue.experiments.simulation.baseline_identity_ids import baseline_identity_ids
from rescue.experiments.simulation.finish_run import finish_run
from rescue.experiments.simulation.install_baseline import install_baseline
from rescue.experiments.simulation.play_event import play_event
from rescue.experiments.simulation.ports import StartRun
from rescue.experiments.simulation.schedule_initial_events import schedule_initial_events
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import Timeline
from rescue.mission.rules import progress
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import DomainValidationError, normalize_id


def simulate(
    scenario: RescueScenario,
    policy: MobilisationPolicy,
    run_id: str,
    *,
    start_run: StartRun,
) -> RunSnapshot:
    """Run a finite scenario from immutable values without touching its source baseline.

    What: validates the scenario, policy and run factory, then runs the scenario in a fresh run and
      returns its finished snapshot.
    When called: by the application's compare service, the demo and the simulation tests.
    Why: each run starts from the scenario's baseline, so the same seed reproduces the same result
      and a source scenario is never changed (spec FR-005).
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    if not isinstance(scenario, RescueScenario):
        raise DomainValidationError("simulate requires a RescueScenario")
    if not isinstance(policy, MobilisationPolicy):
        raise DomainValidationError("simulate requires a MobilisationPolicy")
    if not callable(start_run):
        raise DomainValidationError("simulate requires a callable start_run")
    normalized_run_id = normalize_id(run_id)
    baseline = scenario.baseline
    if not baseline.missions:
        raise DomainValidationError("simulation baseline requires at least one mission")

    started_at = max(Decimal("0"), *(mission.created_at for mission in baseline.missions))
    horizon = started_at + scenario.time_horizon_seconds
    handle = start_run(
        normalized_run_id,
        f"{normalized_run_id}-central",
        policies=(policy,),
        scenarios=(scenario,),
        reserved_ids=baseline_identity_ids(baseline),
    )
    install_baseline(handle, baseline, normalized_run_id)
    session = SimulationSession(
        handle=handle,
        policy=policy,
        timeline=Timeline(horizon=horizon, event_budget=scenario.event_budget),
        rng=random.Random(scenario.seed),
        sequence=itertools.count(1),
        response_rules={
            (rule.ship_id, rule.request_ordinal): rule for rule in scenario.response_rules
        },
        profiles={profile.ship_id: profile for profile in scenario.communication_profiles},
        ship_ordinals={},
    )
    schedule_initial_events(session, baseline, scenario, started_at)
    run_status, finished_at = _play_timeline(session, horizon)
    return finish_run(
        handle, scenario, policy, normalized_run_id, started_at, finished_at, run_status
    )


def _play_timeline(session: SimulationSession, horizon: Decimal) -> tuple[str, Decimal]:
    """Play scheduled events in order until the run completes or the horizon is reached.

    What: pops each event, plays it, and stops early once every mission is confirmed and no later
      event is due at the same instant. Returns the status and the finish instant.
    When called: once by simulate, after the initial events are scheduled.
    Why: a run that is complete stops at the instant it completed, so later events cannot change
      its recorded outcome.
    """
    while (event := session.timeline.pop_next()) is not None:
        play_event(session, event)
        next_event = session.timeline.peek_next()
        if _all_missions_confirmed(session) and (
            next_event is None or next_event.instant > event.instant
        ):
            return "completed", event.instant
    return "horizon_reached", horizon


def _all_missions_confirmed(session: SimulationSession) -> bool:
    """Report whether every mission in the run has its full demand confirmed.

    What: compares each mission's confirmed seats with its demand in the current store snapshot.
    When called: after each played event, by _play_timeline.
    Why: the run completes only when every mission reaches confirmed seats equal to its demand
      (Constitution I).
    """
    missions = session.handle.store.snapshot().missions
    return all(progress(mission).confirmed == mission.people_count for mission in missions)
