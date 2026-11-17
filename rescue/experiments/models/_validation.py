"""Private validation helpers shared by the experiment value models.

What: Holds the frozen-tree check and the finite-tuple coercion.
Why: Keeps one copy of the checks that every experiment value model relies on.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from rescue.values import DomainValidationError


def frozen_tree(value: object) -> bool:
    """Report whether a value is built only from immutable parts.

    What: Returns True for scalars, Decimals, Enums, and tuples or frozen dataclasses made of them.
    Why: Stored experiment values must not be changed after a run captures them.
    """
    if value is None or type(value) in (str, int, bool, bytes) or isinstance(value, Decimal | Enum):
        return True
    if isinstance(value, tuple):
        return all(frozen_tree(item) for item in value)
    from dataclasses import fields, is_dataclass

    if is_dataclass(value):
        params = getattr(type(value), "__dataclass_params__", None)
        return bool(params and params.frozen) and all(
            frozen_tree(getattr(value, field.name)) for field in fields(value)
        )
    return False


def finite_tuple(value: object, field_name: str) -> tuple:
    """Turn a tuple or list into a tuple.

    What: Returns the items as a tuple and raises DomainValidationError for any other type.
    Why: Gives every collection field one immutable shape and one error message.
    """
    if not isinstance(value, (tuple, list)):
        raise DomainValidationError(f"{field_name} must be a finite tuple or list")
    return tuple(value)
