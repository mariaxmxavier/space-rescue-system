"""What: the finite communication scripts for one ship; reordering changes equal-time priority.
When called: a scenario is built with its communication profiles.
Why: scripted delay, loss, duplication and reordering keep message handling deterministic.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.experiments.models._validation import finite_tuple
from rescue.values import DomainValidationError, Instant, normalize_id, normalize_instant


@dataclass(frozen=True, slots=True)
class CommunicationProfile:
    """What: the finite communication scripts for one ship; reordering changes equal-time priority.
    When called: a scenario is built with its communication profiles.
    Why: scripted delay, loss, duplication and reordering keep message handling deterministic.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    profile_id: str
    ship_id: str
    outbound_delay_seconds: Instant
    decision_delay_seconds: Instant
    return_delay_seconds: Instant
    loss_rule: tuple[int, ...] = ()
    duplication_rule: tuple[int, ...] = ()
    reordering_rule: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", normalize_id(self.profile_id))
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        for name in (
            "outbound_delay_seconds",
            "decision_delay_seconds",
            "return_delay_seconds",
        ):
            object.__setattr__(self, name, normalize_instant(getattr(self, name)))
        for name in ("loss_rule", "duplication_rule", "reordering_rule"):
            values = finite_tuple(getattr(self, name), name)
            if any(type(value) is not int or value <= 0 for value in values):
                raise DomainValidationError(f"{name} must contain positive request ordinals")
            if len(values) != len(set(values)):
                raise DomainValidationError(f"{name} request ordinals must be unique")
            object.__setattr__(self, name, values)
        lost = set(self.loss_rule)
        if lost.intersection(self.duplication_rule) or lost.intersection(self.reordering_rule):
            raise DomainValidationError(
                "lost response ordinals cannot also be duplicated or reordered"
            )
