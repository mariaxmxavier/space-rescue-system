"""Runnable demand-ten rescue and policy-comparison demonstration."""

from __future__ import annotations

from dataclasses import dataclass

from rescue.application.contracts import ComparePolicies
from rescue.bootstrap import new_run
from rescue.experiments.models import (
    CommunicationProfile,
    RescueScenario,
    RunBaseline,
    RunSnapshot,
    ScriptedResponse,
)
from rescue.experiments.simulation import simulate
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.mission.models import Mission, MissionData, RequestOutcome
from rescue.mission.rules import progress, register
from rescue.mobilisation.models import MobilisationPolicy


@dataclass(frozen=True, slots=True)
class ScenarioComparison:
    scenario_id: str
    runs: tuple[RunSnapshot, ...]


@dataclass(frozen=True, slots=True)
class DemoReport:
    primary_run: RunSnapshot
    comparisons: tuple[ScenarioComparison, ...]


def _baseline() -> RunBaseline:
    mission = register(
        MissionData(
            mission_id="MISSION-DEMO",
            station_name="Rescue Station",
            people_count=10,
            created_at=0,
        )
    )
    ships = (
        Ship("SHIP-EARLY", "Swift Rescue"),
        Ship("SHIP-LARGE", "Larger Rescue"),
    )
    availability = (
        ShipAvailability("AVAIL-EARLY", "SHIP-EARLY", 6, 2, True, 0),
        ShipAvailability("AVAIL-LARGE", "SHIP-LARGE", 4, 3, True, 0),
    )
    offers = (
        ShipOffer(
            "OFFER-EARLY",
            "MISSION-DEMO",
            "SHIP-EARLY",
            (ShipOfferRevision("REV-EARLY", 1, 6, 2, True, 0),),
        ),
        ShipOffer(
            "OFFER-LARGE",
            "MISSION-DEMO",
            "SHIP-LARGE",
            (ShipOfferRevision("REV-LARGE", 1, 4, 3, True, 0),),
        ),
    )
    return RunBaseline(
        missions=(mission,),
        market=B3Market(
            market_id="MARKET-DEMO",
            ships=ships,
            availabilities=availability,
            offers=offers,
        ),
    )


def _scenario(
    scenario_id: str,
    baseline: RunBaseline,
    *,
    responses: tuple[ScriptedResponse, ...],
    horizon: int = 10,
    availability_changes: tuple[ShipAvailability, ...] = (),
    profiles: tuple[CommunicationProfile, ...] = (),
) -> RescueScenario:
    return RescueScenario(
        scenario_id=scenario_id,
        revision=1,
        name=scenario_id.replace("SCENARIO-", "").replace("-", " ").title(),
        baseline=baseline,
        response_rules=responses,
        availability_changes=availability_changes,
        time_horizon_seconds=horizon,
        seed=29,
        event_budget=100,
        communication_profiles=profiles,
    )


def _policies() -> tuple[MobilisationPolicy, MobilisationPolicy]:
    return (
        MobilisationPolicy(
            policy_id="EARLIEST",
            revision=1,
            name="Earliest arrival",
            selection_criteria="earliest_arrival",
        ),
        MobilisationPolicy(
            policy_id="LARGEST",
            revision=1,
            name="Largest capacity",
            selection_criteria="largest_capacity",
        ),
    )


def _scenarios(baseline: RunBaseline) -> tuple[RescueScenario, ...]:
    ordinary = _scenario(
        "SCENARIO-ORDINARY",
        baseline,
        responses=(
            ScriptedResponse("SHIP-EARLY", 1, RequestOutcome.ACCEPTED),
            ScriptedResponse("SHIP-LARGE", 1, RequestOutcome.ACCEPTED),
        ),
    )
    partial_refusal = _scenario(
        "SCENARIO-PARTIAL-REFUSAL",
        baseline,
        horizon=16,
        responses=(
            ScriptedResponse("SHIP-EARLY", 1, RequestOutcome.PARTIALLY_ACCEPTED, 4),
            ScriptedResponse("SHIP-LARGE", 1, RequestOutcome.REFUSED),
            ScriptedResponse("SHIP-EARLY", 2, RequestOutcome.ACCEPTED),
            ScriptedResponse("SHIP-LARGE", 2, RequestOutcome.ACCEPTED),
        ),
        profiles=(
            CommunicationProfile("PROFILE-EARLY-FAST", "SHIP-EARLY", 1, 1, 1),
            CommunicationProfile("PROFILE-LARGE-SLOW", "SHIP-LARGE", 2, 2, 2),
        ),
    )
    delayed_loss = _scenario(
        "SCENARIO-DELAYED-LOSS",
        baseline,
        horizon=8,
        responses=(
            ScriptedResponse("SHIP-EARLY", 1, RequestOutcome.ACCEPTED),
            ScriptedResponse("SHIP-LARGE", 1, RequestOutcome.ACCEPTED),
        ),
        availability_changes=(
            ShipAvailability("AVAIL-EARLY-REDUCED", "SHIP-EARLY", 5, 4, True, 2),
        ),
        profiles=(
            CommunicationProfile(
                "PROFILE-EARLY-LOSS",
                "SHIP-EARLY",
                0,
                0,
                0,
                loss_rule=(1,),
            ),
            CommunicationProfile(
                "PROFILE-LARGE-DELAY",
                "SHIP-LARGE",
                1,
                1,
                1,
            ),
        ),
    )
    return ordinary, partial_refusal, delayed_loss


def run_demo() -> DemoReport:
    """Run the complete demand-ten example and compare two policies in three scenarios."""
    baseline = _baseline()
    policies = _policies()
    scenarios = _scenarios(baseline)
    partial_refusal = scenarios[1]
    primary_run = simulate(partial_refusal, policies[0], run_id="DEMO-PRIMARY", start_run=new_run)

    comparison_context = new_run(
        "DEMO-COMPARISON",
        "DEMO-COMPARISON-CENTRAL",
        policies=policies,
        scenarios=scenarios,
    )
    comparisons: list[ScenarioComparison] = []
    for scenario in scenarios:
        compared = comparison_context.central.compare(
            ComparePolicies(
                scenario_id=scenario.scenario_id,
                scenario_revision=scenario.revision,
                policy_keys=tuple((policy.policy_id, policy.revision) for policy in policies),
            )
        )
        if compared.status != "applied" or compared.value is None:
            raise RuntimeError(f"policy comparison failed for {scenario.scenario_id}")
        comparisons.append(ScenarioComparison(scenario.scenario_id, compared.value))
    return DemoReport(primary_run, tuple(comparisons))


def _history_lines(mission: Mission) -> tuple[str, ...]:
    """Return one line per applied history entry, in the order the central applied them.

    What: formats each entry's time, action, seat changes and reason.

    When: called by render for the primary run only.

    Why: the brief asks the demo to show how the central follows the situation, step by step.
    """
    return tuple(
        f"  t={entry.recorded_at} {entry.action}: confirmed {entry.confirmed_seats_delta:+d}, "
        f"pending {entry.pending_seats_delta:+d}"
        + ("" if entry.reason == entry.action else f" ({entry.reason})")
        for entry in sorted(mission.history, key=lambda entry: entry.mission_sequence)
    )


def _request_lines(mission: Mission) -> tuple[str, ...]:
    """Return one line per seat request: its ship, the seats asked and confirmed, and its outcome.

    What: lists the mission's requests in the order they were submitted.

    When: called by render for the primary run only.

    Why: shows which ship was asked for how many seats and what came back, so the help still
    missing after a partial acceptance or a refusal is visible.
    """
    return tuple(
        f"  request {request.request_id} to {request.ship_id}: asked {request.requested_seats}, "
        f"confirmed {request.confirmed_seats}, {request.outcome}"
        for request in sorted(
            mission.requests, key=lambda request: (request.submitted_at, request.request_id)
        )
    )


def render(report: DemoReport) -> str:
    """Return the primary run as a step log, followed by the one-line summary.

    What: prints the mission's history and requests, then the confirmed, pending and status
    summary and the comparison count.

    When: called by main, and by the e2e demo test to check the output.

    Why: the demo must show the mobilisation steps, not only the end state. The summary stays the
    last line, so the existing checks on the completed state still apply.
    """
    mission = report.primary_run.missions[0]
    state = progress(mission)
    policy_count = len(report.comparisons[0].runs) if report.comparisons else 0
    summary = (
        "rescue demo: "
        f"confirmed={state.confirmed}, pending={state.pending}, status={state.status}; "
        f"comparisons={len(report.comparisons)} scenarios x {policy_count} policies"
    )
    return "\n".join(
        (
            f"step log: mission {mission.mission_id}, demand {mission.people_count}, "
            f"policy {report.primary_run.run.policy_id}",
            "history:",
            *_history_lines(mission),
            "requests:",
            *_request_lines(mission),
            summary,
        )
    )


def main() -> None:
    print(render(run_demo()))


if __name__ == "__main__":
    main()
