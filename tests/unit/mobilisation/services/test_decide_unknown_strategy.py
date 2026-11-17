"""select_offers rejects a policy whose strategy has no allocator in the injected mapping."""

import pytest

from rescue.mobilisation.services.decide import select_offers
from rescue.values import DomainValidationError


def test_strategy_without_an_allocator_in_the_mapping_is_rejected(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
) -> None:
    candidates = (candidate_factory("A", revision_factory("A-r")),)
    with pytest.raises(DomainValidationError, match="unknown mobilisation strategy"):
        select_offers(
            mission_factory(3),
            candidates,
            policy_factory("knapsack"),
            decision_context_factory(1),
            allocators={},
        )
