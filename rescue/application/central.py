"""The RescueCentral facade over the application services.

What: holds the ports of a run and hands every public call to the service that owns the use case.
When called: constructed by new_run; its methods are called by the demo, the experiments and the tests.
Why: callers keep one stable entry point while each use case lives in its own small service.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.adapters.ports import Clock, IdSource, Simulator, TransactionStore
from rescue.application.contracts import (
    AcceptQuote,
    CancelRequest,
    ComparePolicies,
    CreateRequest,
    ExpireRequest,
    Mobilise,
    PublishAvailability,
    PublishOffer,
    RecordQuote,
    RecordResponse,
    RecoverReports,
    RegisterMission,
    RegisterShip,
    RejectQuote,
    RequestQuotes,
    Result,
    SynchroniseInbound,
)
from rescue.application.contracts.snapshots import (
    AvailabilitySnapshot,
    DecisionSnapshot,
    MissionSnapshot,
    OfferSnapshot,
    QuoteSnapshot,
    RequestSnapshot,
    RFQSnapshot,
    ShipSnapshot,
)
from rescue.application.services.communication.get_deliveries import get_deliveries
from rescue.application.services.communication.get_session import get_session
from rescue.application.services.communication.record_response import record_response
from rescue.application.services.communication.recover_reports import recover_reports
from rescue.application.services.communication.synchronise_inbound import synchronise_inbound
from rescue.application.services.comparison.compare_policies import compare_policies
from rescue.application.services.fleet.publish_availability import publish_availability
from rescue.application.services.fleet.publish_offer import publish_offer
from rescue.application.services.fleet.register_ship import register_ship
from rescue.application.services.missions.get_history import get_history
from rescue.application.services.missions.get_progress import get_progress
from rescue.application.services.missions.register_mission import register_mission
from rescue.application.services.mobilisation.get_decision import get_decision
from rescue.application.services.mobilisation.mobilise import mobilise
from rescue.application.services.quotes.accept_quote import accept_quote
from rescue.application.services.quotes.expire_quotes import expire_quotes
from rescue.application.services.quotes.record_quote import record_quote
from rescue.application.services.quotes.reject_quote import reject_quote
from rescue.application.services.quotes.request_quotes import request_quotes
from rescue.application.services.requests.cancel_request import cancel_request
from rescue.application.services.requests.create_request import create_request
from rescue.application.services.requests.expire_request import expire_request
from rescue.communication.models import (
    CommunicationSession,
    DecisionReport,
    MessageDelivery,
    SequenceControl,
)
from rescue.experiments.models import RunSnapshot
from rescue.mission.models import MissionProgress, RequestHistoryEntry


@dataclass(frozen=True, slots=True)
class RescueCentral:
    """The facade through which callers run the application.

    What: holds the run ids and the store, clock, id source and simulator ports, and forwards each public method to its service.
    When called: built by new_run in bootstrap; used by the demo, the experiments and the tests.
    Why: callers keep one stable entry point while the use cases live in their own services.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    application_run_id: str
    central_id: str
    store: TransactionStore
    clock: Clock
    id_source: IdSource
    simulator: Simulator

    def register_mission(self, command: RegisterMission) -> Result[MissionSnapshot]:
        """Registers one mission from the command.

        What: registers one mission from the command.
        When called: by callers that open a rescue mission, such as the demo and the integration tests.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return register_mission(command, store=self.store)

    def register_ship(self, command: RegisterShip) -> Result[ShipSnapshot]:
        """Registers one ship in the market of the run.

        What: registers one ship in the market of the run.
        When called: by callers that add a ship before publishing its availability.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return register_ship(command, store=self.store)

    def publish_availability(self, command: PublishAvailability) -> Result[AvailabilitySnapshot]:
        """Publishes one ship availability.

        What: publishes one ship availability.
        When called: by callers that report that a ship can or cannot take people.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return publish_availability(command, store=self.store)

    def publish_offer(self, command: PublishOffer) -> Result[OfferSnapshot]:
        """Publishes one offer revision for a mission and ship.

        What: publishes one offer revision for a mission and ship.
        When called: by callers that let a ship offer seats to a mission.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return publish_offer(command, store=self.store)

    def request_quotes(self, command: RequestQuotes) -> Result[tuple[RFQSnapshot, ...]]:
        """Sends a request for quote to every ship that can help.

        What: sends a request for quote to every ship that can help.
        When called: by callers that need seats for a mission and want ship quotes.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return request_quotes(command, store=self.store, id_source=self.id_source)

    def record_quote(self, command: RecordQuote) -> Result[QuoteSnapshot]:
        """Records and holds one ship quote.

        What: records and holds one ship quote.
        When called: by callers that deliver the answer of a ship to a request for quote.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return record_quote(command, store=self.store)

    def accept_quote(self, command: AcceptQuote) -> Result[RequestSnapshot]:
        """Accepts a held quote and creates its seat request.

        What: accepts a held quote and creates its seat request.
        When called: by callers that choose a ship quote for a mission.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return accept_quote(command, store=self.store, id_source=self.id_source)

    def create_request(self, command: CreateRequest) -> Result[RequestSnapshot]:
        """Creates one seat request without a quote.

        What: creates one seat request without a quote.
        When called: by callers that ask a ship for seats directly.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return create_request(command, store=self.store, id_source=self.id_source)

    def reject_quote(self, command: RejectQuote) -> Result[QuoteSnapshot]:
        """Closes a held quote as rejected.

        What: closes a held quote as rejected.
        When called: by callers that turn down a ship quote.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return reject_quote(command, store=self.store)

    def expire_quotes(self, now) -> Result[tuple[str, ...]]:
        """Expires every held quote and pending request for quote past its time.

        What: expires every held quote and pending request for quote past its time.
        When called: by callers that advance the clock and want stale quotes closed.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return expire_quotes(now, store=self.store)

    def cancel_request(self, command: CancelRequest) -> Result[RequestSnapshot]:
        """Cancels one pending seat request.

        What: cancels one pending seat request.
        When called: by callers that withdraw a request before the ship answers.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return cancel_request(command, store=self.store, id_source=self.id_source)

    def expire_request(self, command: ExpireRequest) -> Result[RequestSnapshot]:
        """Expires one pending seat request whose deadline has passed.

        What: expires one pending seat request whose deadline has passed.
        When called: by callers that advance the clock past a request deadline.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return expire_request(command, store=self.store, id_source=self.id_source)

    def record_response(self, command: RecordResponse) -> Result[RequestSnapshot]:
        """Records one ship response delivery and applies it to the request when the rules allow.

        What: records one ship response delivery and applies it to the request when the rules allow.
        When called: once per inbound ship response attempt, including lost and repeated ones.
        Why: the facade only forwards; classification and sequencing live in the service and the communication rules.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
        """
        return record_response(command, store=self.store, id_source=self.id_source)

    def recover_reports(
        self, command: RecoverReports
    ) -> Result[tuple[DecisionReport | SequenceControl, ...]]:
        """Replays the retained decision reports of a session, then the control for the live stream.

        What: replays the retained decision reports of a session, then the control for the live stream.
        When called: when a ship has missed decision reports and asks for them again.
        Why: the facade only forwards, and recovery only reads retained reports.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
        """
        return recover_reports(command, store=self.store)

    def synchronise_inbound(self, command: SynchroniseInbound) -> Result[CommunicationSession]:
        """Moves the expected inbound number of a session forward to the one the ship will send next.

        What: moves the expected inbound number of a session forward to the one the ship will send next.
        When called: when a ship skips inbound numbers and tells central where it resumes.
        Why: the facade only forwards, so the skipped range becomes a visible gap in the service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
        """
        return synchronise_inbound(command, store=self.store)

    def get_session(self, session_id: str) -> Result[CommunicationSession]:
        """Returns one session for diagnostics.

        What: returns one session for diagnostics.
        When called: by tests and operators inspecting the sequenced exchange of a ship.
        Why: the facade only forwards; an absent session is a named rejection in the service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
        """
        return get_session(session_id, store=self.store)

    def get_progress(self, mission_id: str, now) -> Result[MissionProgress]:
        """Returns the progress of one mission.

        What: returns the progress of one mission.
        When called: by callers that show how many seats a mission still needs.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return get_progress(mission_id, now, store=self.store)

    def get_history(self, mission_id: str) -> Result[tuple[RequestHistoryEntry, ...]]:
        """Returns the request history of one mission.

        What: returns the request history of one mission.
        When called: by callers that audit what happened to the requests of a mission.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return get_history(mission_id, store=self.store)

    def get_decision(self, decision_id: str) -> Result[DecisionSnapshot]:
        """Returns one recorded mobilisation decision.

        What: returns one recorded mobilisation decision.
        When called: by callers that read back why ships were chosen.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return get_decision(decision_id, store=self.store)

    def get_deliveries(self, message_id: str) -> Result[tuple[MessageDelivery, ...]]:
        """Returns every recorded delivery of one message.

        What: returns every recorded delivery of one message.
        When called: by tests and operators tracing a message through its attempts.
        Why: the facade only forwards; an unknown message is a named rejection in the service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
        """
        return get_deliveries(message_id, store=self.store)

    def compare(self, command: ComparePolicies) -> Result[tuple[RunSnapshot, ...]]:
        """Runs the configured policies against one immutable scenario revision.

        What: runs the configured policies against one immutable scenario revision.
        When called: by callers that compare mobilisation policies on one scenario.
        Why: the facade only forwards; the simulator port keeps the application off the experiment runner.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return compare_policies(
            command, store=self.store, id_source=self.id_source, simulator=self.simulator
        )

    def mobilise(self, command: Mobilise) -> Result[DecisionSnapshot]:
        """Selects ship offers for a mission under a policy and records the decision.

        What: selects ship offers for a mission under a policy and records the decision.
        When called: by callers that decide which ships to mobilise.
        Why: the facade only forwards, so the use case lives in one service.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return mobilise(command, store=self.store, id_source=self.id_source)
