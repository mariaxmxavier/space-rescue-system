"""Stable evidence identities for the twelve simulated situations."""

from enum import StrEnum


class SituationId(StrEnum):
    """Name a situation independently from its display label for recipe evidence."""

    FULL_CONFIRMATION = "full_confirmation"
    PARTIAL_AND_REFUSAL = "partial_and_refusal"
    CANCELLATION = "cancellation"
    EXPIRATION = "expiration"
    DUPLICATE_RESPONSE = "duplicate_response"
    DELAYED_RESPONSE = "delayed_response"
    OUT_OF_ORDER = "out_of_order"
    INVALID_QUANTITY = "invalid_quantity"
    CLOSED_REQUEST_RESPONSE = "closed_request_response"
    SIMULTANEOUS_OPERATIONS = "simultaneous_operations"
    INSUFFICIENT_CAPACITY = "insufficient_capacity"
    AVAILABILITY_CHANGE = "availability_change"
