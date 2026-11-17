"""Mobilisation policy: the named, versioned rule that guides ship selection.

Persisted entity. Diagram class: MobilisationPolicy; UML and ER diagrams under
docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation/.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.values import (
    DomainValidationError,
    Id,
    immutable_tuple,
    normalize_id,
    normalize_positive_quantity,
)


def _name(value: object, field_name: str) -> str:
    """Return a nonblank string unchanged, or raise a validation error naming the field."""
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be a nonblank string")
    return value


def _selection_criteria(value: object) -> str | tuple[tuple[str, str], ...]:
    """Keep policy configuration immutable while allowing a named strategy."""
    if isinstance(value, str):
        return _name(value, "selection criteria")
    if isinstance(value, dict):
        value = tuple(value.items())
    try:
        criteria = immutable_tuple(value)
    except TypeError as error:
        raise DomainValidationError(
            "selection criteria must be a strategy name or key/value pairs"
        ) from error
    normalized: list[tuple[str, str]] = []
    for item in criteria:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DomainValidationError("selection criteria entries must be key/value pairs")
        key = _name(item[0], "selection criteria key")
        entry = _name(item[1], "selection criteria value")
        normalized.append((key, entry))
    return tuple(sorted(normalized))


def _algorithm(value: str) -> AlgorithmName:
    """Resolve a strategy string to an AlgorithmName or raise a validation error."""
    try:
        return AlgorithmName(value)
    except ValueError:
        raise DomainValidationError(f"unknown mobilisation strategy: {value!r}") from None


@dataclass(frozen=True, slots=True)
class MobilisationPolicy:
    """A named, versioned rule for choosing ships to mobilise, cited by every decision.

    Created when a policy is configured and read each time a decision is made. It keeps
    the selection strategy explicit so a decision can name the exact policy revision it
    applied. Diagram class: MobilisationPolicy.
    """

    policy_id: Id
    revision: int
    name: str
    selection_criteria: str | tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", normalize_id(self.policy_id))
        object.__setattr__(self, "revision", normalize_positive_quantity(self.revision))
        object.__setattr__(self, "name", _name(self.name, "policy name"))
        object.__setattr__(self, "selection_criteria", _selection_criteria(self.selection_criteria))
        self.strategy

    @property
    def strategy(self) -> AlgorithmName:
        """Resolve the selection criteria to an AlgorithmName, or fail if none is named."""
        if isinstance(self.selection_criteria, str):
            return _algorithm(self.selection_criteria)
        criteria = dict(self.selection_criteria)
        strategy = criteria.get("strategy")
        if strategy is None and len(criteria) == 1:
            strategy = next(iter(criteria.values()))
        if strategy is None:
            raise DomainValidationError("selection criteria must name a strategy")
        return _algorithm(strategy)
