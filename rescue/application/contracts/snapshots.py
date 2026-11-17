"""Names for the read-only views a command result can carry.

What: aliases that name the domain record each Result value holds.
When called: imported by services and callers that type or read a Result value.
Why: callers name the view they get without importing the domain models behind it.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import RFQOffer
from rescue.mission.models import Mission, SeatRequest
from rescue.mobilisation.models import MobilisationDecision

MissionSnapshot = Mission
ShipSnapshot = Ship
AvailabilitySnapshot = ShipAvailability
OfferSnapshot = ShipOffer
RFQSnapshot = SeatRFQ
QuoteSnapshot = RFQOffer
RequestSnapshot = SeatRequest
DecisionSnapshot = MobilisationDecision
