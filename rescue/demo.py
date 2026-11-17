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
from rescue.experiments.runner import simulate
from rescue.market.models import (
    B3Market,
    Ship,
    ShipAvailability,
    ShipOffer,
    ShipOfferRevision,
)
from rescue.mission.models import MissionData, RequestOutcome
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
        responses=(
            ScriptedResponse("SHIP-EARLY", 1, RequestOutcome.PARTIALLY_ACCEPTED, 4),
            ScriptedResponse("SHIP-LARGE", 1, RequestOutcome.REFUSED),
            ScriptedResponse("SHIP-EARLY", 2, RequestOutcome.ACCEPTED),
            ScriptedResponse("SHIP-LARGE", 2, RequestOutcome.ACCEPTED),
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
    primary_run = simulate(partial_refusal, policies[0], run_id="DEMO-PRIMARY")

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


def render(report: DemoReport) -> str:
    """Return a concise, stable summary suitable for the command-line demo."""
    state = progress(report.primary_run.missions[0])
    policy_count = len(report.comparisons[0].runs) if report.comparisons else 0
    return (
        "rescue demo: "
        f"confirmed={state.confirmed}, pending={state.pending}, status={state.status}; "
        f"comparisons={len(report.comparisons)} scenarios x {policy_count} policies"
    )


def main() -> None:
    print(render(run_demo()))


if __name__ == "__main__":
    main()
