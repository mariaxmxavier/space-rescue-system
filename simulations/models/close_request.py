"""Timeline action closing a request identified at runtime."""

from typing import Literal

from simulations.models.base import StrictModel
from simulations.models.close_kind import CloseKind
from simulations.models.request_selector import RequestSelector


class CloseRequest(StrictModel):
    """Cancel or expire a request using a selector bound to an actual response ID."""

    kind: Literal["close_request"] = "close_request"
    request: RequestSelector
    close_as: CloseKind
