"""The state of one simulation run.

What: the frozen `SimulationSession` that groups the run handle, policy, timeline and counters.
When called: built once per scenario run and passed to every runner step.
Why: one immutable bundle replaces scattered closure variables, so each step names what it uses.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

import random
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from rescue.experiments.models import CommunicationProfile, ScriptedResponse
from rescue.experiments.simulation.ports import RunHandle
from rescue.experiments.timeline import Timeline
from rescue.mobilisation.models import MobilisationPolicy


@dataclass(frozen=True)
class SimulationSession:
    """The state of one simulation run.

    What: the run handle, policy, timeline, random source, id sequence, response rules,
      communication profiles and ship ordinals.
    When called: created when a scenario starts and read by each runner step.
    Why: the fields themselves are fixed while the timeline, sequence and ordinals advance.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    handle: RunHandle
    policy: MobilisationPolicy
    timeline: Timeline
    rng: random.Random
    sequence: Iterator[int]
    response_rules: Mapping[tuple[str, int], ScriptedResponse]
    profiles: Mapping[str, CommunicationProfile]
    ship_ordinals: dict[str, int]
