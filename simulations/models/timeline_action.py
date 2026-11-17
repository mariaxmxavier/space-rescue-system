"""Discriminated union of semantic virtual-timeline actions."""

from typing import Annotated, TypeAlias

from pydantic import Field

from simulations.models.close_request import CloseRequest
from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.observe import Observe
from simulations.models.publish_fleet import PublishFleet
from simulations.models.ship_reply import ShipReply
from simulations.models.solver_round import SolverRound

TimelineAction: TypeAlias = Annotated[
    PublishFleet | SolverRound | ShipReply | CloseRequest | ConcurrentRequests | Observe,
    Field(discriminator="kind"),
]
