"""Translate JSON values to and from the application's immutable values."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import UnionType
from typing import TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")


class PayloadError(ValueError):
    """A request payload does not match the declared application contract."""


def to_json_value(value: object) -> object:
    """Convert supported application values to lossless JSON-compatible values."""
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise PayloadError("non-finite decimals cannot be encoded")
        return str(value)
    if isinstance(value, Enum):
        return to_json_value(value.value)
    if isinstance(value, tuple):
        return [to_json_value(item) for item in value]
    if isinstance(value, list):
        return [to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_json_value(getattr(value, field.name)) for field in fields(value)}
    raise PayloadError(f"unsupported response value: {type(value).__name__}")


def from_json_value(value: object, expected_type: type[T]) -> T:
    """Build a declared immutable value from JSON data, rejecting unknown fields."""
    return _decode(value, expected_type)


def _decode(value: object, expected_type: object) -> object:
    origin = get_origin(expected_type)
    args = get_args(expected_type)
    if expected_type is object:
        return value
    if origin in (Union, UnionType):
        if value is None and type(None) in args:
            return None
        for option in args:
            if option is type(None):
                continue
            try:
                return _decode(value, option)
            except PayloadError:
                continue
        raise PayloadError("value does not match any allowed type")
    if expected_type is Decimal:
        if type(value) not in (int, str):
            raise PayloadError("decimal values must be integers or decimal strings")
        try:
            result = Decimal(value)
        except InvalidOperation, ValueError:
            raise PayloadError("invalid decimal value") from None
        if not result.is_finite():
            raise PayloadError("decimal values must be finite")
        return result
    if origin is tuple:
        if not isinstance(value, list):
            raise PayloadError("tuple values must be JSON arrays")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode(item, args[0]) for item in value)
        if len(value) != len(args):
            raise PayloadError("tuple length does not match the contract")
        return tuple(_decode(item, item_type) for item, item_type in zip(value, args, strict=True))
    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        try:
            return expected_type(value)
        except TypeError, ValueError:
            raise PayloadError(f"invalid {expected_type.__name__} value") from None
    if isinstance(expected_type, type) and is_dataclass(expected_type):
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise PayloadError(f"{expected_type.__name__} must be a JSON object")
        model_fields = {field.name: field for field in fields(expected_type)}
        extra = value.keys() - model_fields.keys()
        if extra:
            raise PayloadError(
                f"unknown fields for {expected_type.__name__}: {', '.join(sorted(extra))}"
            )
        hints = get_type_hints(expected_type)
        missing = [
            name
            for name, field in model_fields.items()
            if name not in value and field.default is field.default_factory
        ]
        if missing:
            raise PayloadError(f"missing fields for {expected_type.__name__}: {', '.join(missing)}")
        decoded = {
            name: _decode(item, hints.get(name, model_fields[name].type))
            for name, item in value.items()
        }
        try:
            return expected_type(**decoded)
        except (TypeError, ValueError) as error:
            raise PayloadError(str(error)) from None
    if expected_type is int and type(value) is not int:
        raise PayloadError("value must be an integer")
    if expected_type is bool and type(value) is not bool:
        raise PayloadError("value must be a boolean")
    if expected_type is str and not isinstance(value, str):
        raise PayloadError("value must be a string")
    if isinstance(expected_type, type) and not isinstance(value, expected_type):
        raise PayloadError(f"value must be {expected_type.__name__}")
    return value
