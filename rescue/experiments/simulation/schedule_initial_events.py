"""Seed the timeline before the run starts.

What: `schedule_initial_events` queues the first mobilisations, availability changes and the
  baseline's pending request events.
When called: by the runner once, after the baseline is installed.
Why: the run needs its opening events on the timeline before the first event is popped.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from rescue.experiments.models import RescueScenario, RunBaseline
from rescue.experiments.simulation.schedule_response import schedule_response
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent
from rescue.mission.models import RequestOutcome


def schedule_initial_events(
    session: SimulationSession,
    baseline: RunBaseline,
    scenario: RescueScenario,
    started_at: Decimal,
) -> None:
    """Seed the timeline before the run starts.

    What: schedules a mobilise event per mission, then each availability change shifted by
      `started_at`, then for each pending baseline request an expire event at the later of
      `started_at` and its deadline, followed by its scripted response when a rule matches.
    When called: once per run, before the event loop.
    Why: sequence numbers follow this order, so equal-time events replay the same way every run.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    timeline = session.timeline
    for mission in baseline.missions:
        timeline.schedule(
            TimelineEvent(
                instant=started_at,
                kind="mobilise",
                scenario_sequence=next(session.sequence),
                payload=mission.mission_id,
            )
        )
    for availability in scenario.availability_changes:
        scheduled_at = started_at + availability.recorded_at
        timeline.schedule(
            TimelineEvent(
                instant=scheduled_at,
                kind="availability",
                scenario_sequence=next(session.sequence),
                payload=replace(availability, recorded_at=scheduled_at),
            )
        )
    _schedule_baseline_requests(session, baseline, started_at)


def _schedule_baseline_requests(
    session: SimulationSession, baseline: RunBaseline, started_at: Decimal
) -> None:
    """Queue the expire and response events of the baseline's pending requests.

    What: walks the baseline missions in order, counts each request toward its ship's ordinal,
      and for each pending request queues its expire event and, when a rule matches, its
      response.
    When called: by schedule_initial_events after the mobilise and availability events.
    Why: ship ordinals must count every request of the baseline in order, so each scripted
      response attaches to the request it was written for.
    """
    timeline = session.timeline
    ordinals = session.ship_ordinals
    for mission in baseline.missions:
        for request in mission.requests:
            ordinals[request.ship_id] = ordinals.get(request.ship_id, 0) + 1
            if request.outcome != RequestOutcome.PENDING:
                continue
            if request.response_deadline is not None:
                timeline.schedule(
                    TimelineEvent(
                        instant=max(started_at, request.response_deadline),
                        kind="expire",
                        scenario_sequence=next(session.sequence),
                        payload=(mission.mission_id, request.request_id),
                    )
                )
            rule = session.response_rules.get((request.ship_id, ordinals[request.ship_id]))
            if rule is not None:
                schedule_response(
                    session,
                    rule,
                    mission,
                    request,
                    ordinals[request.ship_id],
                    session.profiles.get(request.ship_id),
                    session.handle.id_source.next_id("message"),
                )
