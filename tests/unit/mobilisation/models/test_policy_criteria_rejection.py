"""Policy construction rejects selection criteria that are neither a strategy name nor key/value pairs."""

import pytest

from rescue.mobilisation.models.policy import MobilisationPolicy
from rescue.values import DomainValidationError


def test_criteria_that_is_not_a_name_or_pairs_is_rejected_at_construction() -> None:
    with pytest.raises(DomainValidationError, match="strategy name or key/value pairs"):
        MobilisationPolicy(policy_id="policy-1", revision=1, name="Policy", selection_criteria=12)
