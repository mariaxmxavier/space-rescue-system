from __future__ import annotations

import dataclasses

import pytest

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.values import DomainValidationError


def test_allocation_keeps_ship_and_seats():
    allocation = Allocation(ship_id="A", seats=3)

    assert (allocation.ship_id, allocation.seats) == ("A", 3)


def test_allocation_accepts_zero_seats():
    assert Allocation(ship_id="A", seats=0).seats == 0


@pytest.mark.parametrize("seats", [-1, -10])
def test_allocation_rejects_negative_seats(seats):
    with pytest.raises(DomainValidationError):
        Allocation(ship_id="A", seats=seats)


@pytest.mark.parametrize("seats", [1.5, "2", None, True])
def test_allocation_rejects_non_integer_seats(seats):
    with pytest.raises(DomainValidationError):
        Allocation(ship_id="A", seats=seats)


def test_allocation_rejects_blank_ship_id():
    with pytest.raises(DomainValidationError):
        Allocation(ship_id=" ", seats=1)


def test_allocation_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        Allocation(ship_id="A", seats=1).seats = 2


def test_allocation_result_keeps_algorithm_allocations_and_trace_in_order():
    allocations = (Allocation("B", 2), Allocation("A", 1))

    result = AllocationResult(
        algorithm=AlgorithmName.EARLIEST_ARRIVAL, allocations=allocations, trace=()
    )

    assert result.algorithm is AlgorithmName.EARLIEST_ARRIVAL
    assert result.allocations == allocations
    assert result.trace == ()
