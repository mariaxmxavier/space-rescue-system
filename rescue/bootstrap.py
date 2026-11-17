"""Construct one isolated callable application context per run."""

from __future__ import annotations

from dataclasses import dataclass

from rescue.adapters.memory import MemoryTransactionStore, SequenceIdSource, ZeroClock
from rescue.adapters.ports import Clock, IdSource, TransactionStore
from rescue.application.central import RescueCentral
from rescue.experiments.models import RescueScenario
from rescue.experiments.simulator import RunnerSimulator
from rescue.market.models.b3_market import B3Market
from rescue.mobilisation.models import MobilisationPolicy
from rescue.state import RunState
from rescue.values import DomainValidationError, Id, normalize_id


@dataclass(frozen=True, slots=True)
class RunContext:
    application_run_id: Id
    central_id: Id
    store: TransactionStore
    clock: Clock
    id_source: IdSource
    central: RescueCentral


def new_run(
    application_run_id: Id,
    central_id: Id,
    *,
    clock: Clock | None = None,
    id_source: IdSource | None = None,
    policies: tuple[MobilisationPolicy, ...] = (),
    scenarios: tuple[RescueScenario, ...] = (),
    reserved_ids: tuple[Id, ...] = (),
) -> RunContext:
    """Create an empty run with no process-global registry or shared state.

    ``reserved_ids`` seeds the default sequence source when a caller clones
    existing values into the run.
    """
    run_id = normalize_id(application_run_id)
    normalized_central_id = normalize_id(central_id)
    if not isinstance(policies, (tuple, list)) or not isinstance(scenarios, (tuple, list)):
        raise DomainValidationError("policies and scenarios must be finite collections")
    if not isinstance(reserved_ids, (tuple, list)):
        raise DomainValidationError("reserved_ids must be a finite tuple or list")
    normalized_reserved_ids = tuple(normalize_id(value) for value in reserved_ids)
    policy_values = tuple(policies)
    scenario_values = tuple(scenarios)
    if any(not isinstance(policy, MobilisationPolicy) for policy in policy_values):
        raise DomainValidationError("policies must contain MobilisationPolicy values")
    if any(not isinstance(scenario, RescueScenario) for scenario in scenario_values):
        raise DomainValidationError("scenarios must contain RescueScenario values")
    policy_keys = tuple((policy.policy_id, policy.revision) for policy in policy_values)
    scenario_keys = tuple((scenario.scenario_id, scenario.revision) for scenario in scenario_values)
    if len(policy_keys) != len(set(policy_keys)):
        raise DomainValidationError("policy identity and revision pairs must be unique")
    if len(scenario_keys) != len(set(scenario_keys)):
        raise DomainValidationError("scenario identity and revision pairs must be unique")
    run_state = RunState(
        application_run_id=run_id,
        central_id=normalized_central_id,
        market=B3Market(market_id=f"{normalized_central_id}-market"),
        policies=policy_values,
        scenarios=scenario_values,
    )
    store = MemoryTransactionStore(run_state)
    selected_clock = clock if clock is not None else ZeroClock()
    selected_ids = id_source if id_source is not None else SequenceIdSource(normalized_reserved_ids)
    central = RescueCentral(
        application_run_id=run_id,
        central_id=normalized_central_id,
        store=store,
        clock=selected_clock,
        id_source=selected_ids,
        simulator=RunnerSimulator(),
    )
    return RunContext(
        application_run_id=run_id,
        central_id=normalized_central_id,
        store=store,
        clock=selected_clock,
        id_source=selected_ids,
        central=central,
    )
