"""The five central operations the simulation runner calls.

What: a Protocol listing `mobilise`, `create_request`, `publish_availability`, `expire_request` and
  `record_response`, typed with the application commands and `Result`.
When called: used as the type of `RunHandle.central`; the runner calls its five methods while it
  replays a scenario.
Why: naming only the methods the runner uses lets experiments avoid importing the central, which
  would create an import cycle; any central with these methods satisfies it.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from typing import Protocol

from rescue.application.contracts import (
    CreateRequest,
    ExpireRequest,
    Mobilise,
    PublishAvailability,
    RecordResponse,
    Result,
)
from rescue.market.models.availability import ShipAvailability
from rescue.mission.models import SeatRequest
from rescue.mobilisation.models import MobilisationDecision


class SimulationCentral(Protocol):
    """The five central operations the simulation runner calls.

    What: the methods `mobilise`, `create_request`, `publish_availability`, `expire_request` and
      `record_response`, each taking one command and returning a `Result`.
    When called: held by a `RunHandle`; the runner calls each method as scenario events fire.
    Why: it is the narrow slice of the central the runner needs, so experiments stays independent
      of the application's central module.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    def mobilise(self, command: Mobilise) -> Result[MobilisationDecision]: ...

    def create_request(self, command: CreateRequest) -> Result[SeatRequest]: ...

    def publish_availability(self, command: PublishAvailability) -> Result[ShipAvailability]: ...

    def expire_request(self, command: ExpireRequest) -> Result[SeatRequest]: ...

    def record_response(self, command: RecordResponse) -> Result[SeatRequest]: ...
