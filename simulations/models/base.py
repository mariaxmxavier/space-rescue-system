"""Shared immutable validation base for simulation contracts."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Validate a strict immutable simulation value when it crosses a contract boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
