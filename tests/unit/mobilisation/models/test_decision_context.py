from __future__ import annotations

import pytest

from rescue.mobilisation import models
from rescue.mobilisation.models.decision_context import DecisionContext
from rescue.values import DomainValidationError


def test_decision_context_is_importable_from_the_package_path():
    assert models.DecisionContext is DecisionContext


def test_decision_context_turns_evaluation_ids_into_a_tuple():
    context = DecisionContext("d1", 5, ["e1", "e2"])

    assert context.evaluation_ids == ("e1", "e2")
    assert context.time == context.recorded_at == 5


def test_decision_context_rejects_duplicate_evaluation_ids():
    with pytest.raises(DomainValidationError, match="evaluation IDs must be unique"):
        DecisionContext("d1", 0, ("e1", "e1"))


def test_decision_context_rejects_blank_evaluation_id():
    with pytest.raises(DomainValidationError):
        DecisionContext("d1", 0, ("e1", " "))


def test_decision_context_rejects_blank_decision_id():
    with pytest.raises(DomainValidationError):
        DecisionContext(" ", 0, ())
