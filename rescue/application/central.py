"""Transactional RescueCentral orchestration over domain-owned values."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, TypeVar

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
    RegisterMission,
    RegisterShip,
    RejectQuote,
    RequestQuotes,
    Result,
)
from rescue.application.ports import Clock, IdSource, TransactionStore
from rescue.application.state import RunState
from rescue.communication.models import CommunicationMessage, MessageDelivery
from rescue.market import rules as market_rules
from rescue.market.models import (
    RFQOffer,
    SeatRFQ,
    Ship,
    ShipAvailability,
    ShipOffer,
    ShipOfferRevision,
)
from rescue.mission import rules as mission_rules
from rescue.mission.models import (
    Mission,
    MissionData,
    MissionProgress,
    RequestHistoryEntry,
    SeatRequest,
)
from rescue.mobilisation.models import (
    Candidate,
    DecisionContext,
    MobilisationDecision,
    MobilisationPolicy,
)
from rescue.mobilisation.services.decide import select_offers
from rescue.values import (
    DomainValidationError,
    TransitionContext,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)

if TYPE_CHECKING:
    from rescue.experiments.models import RunSnapshot

T = TypeVar("T")
MissionSnapshot = Mission
ShipSnapshot = Ship
AvailabilitySnapshot = ShipAvailability
OfferSnapshot = ShipOffer
RFQSnapshot = SeatRFQ
QuoteSnapshot = RFQOffer
RequestSnapshot = SeatRequest
DecisionSnapshot = MobilisationDecision


def _mission(state: RunState, mission_id: str) -> Mission | None:
    normalized = normalize_id(mission_id)
    return next((item for item in state.missions if item.mission_id == normalized), None)


def _set_mission(state: RunState, mission: Mission) -> RunState:
    if not any(item.mission_id == mission.mission_id for item in state.missions):
        raise DomainValidationError("cannot update an unregistered mission")
    return replace(
        state,
        missions=tuple(
            mission if item.mission_id == mission.mission_id else item for item in state.missions
        ),
    )


def _result(status: str, value=None, reason: str | None = None) -> Result:
    return Result(status=status, value=value, reason=reason)


def _reason(error: Exception) -> str:
    message = str(error).casefold()
    if "unknown mission" in message or "mission" in message and "unknown" in message:
        return "unknown_mission"
    if "unknown ship" in message or "ship" in message and "unknown" in message:
        return "unknown_ship"
    if "unknown request" in message or "request" in message and "unknown" in message:
        return "unknown_request"
    if "demand" in message:
        return "insufficient_demand"
    if "capacity" in message or "shortfall" in message:
        return "insufficient_capacity"
    if "unavailable" in message:
        return "unavailable"
    if "expired" in message or "expiry" in message:
        return "expired_quote"
    if "revision" in message:
        return "revision_conflict"
    if "closed" in message or "terminal" in message:
        return "closed_request"
    return "invalid_input"


def _offer_revision(state: RunState, mission_id: str, ship_id: str, revision_id: str):
    for offer in state.market.offers:
        if offer.mission_id == mission_id and offer.ship_id == ship_id:
            for revision in offer.revisions:
                if revision.revision_id == revision_id:
                    return revision
    return None


def _request_capacity_reason(
    state: RunState,
    mission: Mission,
    ship_id: str,
    quantity: int,
    revision_id: str,
) -> str | None:
    ship = next((item for item in state.market.ships if item.ship_id == ship_id), None)
    if ship is None:
        return "unknown_ship"
    revision = _offer_revision(state, mission.mission_id, ship_id, revision_id)
    if revision is None:
        return "revision_conflict"
    if not revision.available:
        return "unavailable"
    try:
        latest = market_rules.latest_availability(state.market, ship_id)
    except DomainValidationError:
        return "unknown_ship"
    if latest is None or not latest.available:
        return "unavailable"
    try:
        inventory = market_rules.usage(state.market, state.missions, ship_id)
    except DomainValidationError:
        return "invalid_input"
    if inventory.shortfall or quantity > inventory.free:
        return "insufficient_capacity"
    revision_usage = sum(
        request.requested_seats if request.outcome == "pending" else request.confirmed_seats
        for current_mission in state.missions
        for request in current_mission.requests
        if request.revision_id == revision_id
        and request.outcome in {"pending", "accepted", "partially_accepted"}
    )
    if quantity > max(0, revision.capacity - revision_usage):
        return "insufficient_capacity"
    return None


def _find_quote(state: RunState, quote_id: str) -> RFQOffer | None:
    return next((item for item in state.market.quotes if item.offer_id == quote_id), None)


def _find_rfq(state: RunState, rfq_id: str) -> SeatRFQ | None:
    return next((item for item in state.market.rfqs if item.rfq_id == rfq_id), None)


def _command_entry(state: RunState, command_id: str):
    return next(
        (
            item
            for item in state.command_index
            if isinstance(item, tuple)
            and len(item) == 5
            and item[0] == state.application_run_id
            and item[1] == command_id
        ),
        None,
    )


def _decision_link_reason(
    state: RunState,
    decision_id: str | None,
    mission_id: str,
    ship_id: str,
    requested_seats: int,
    revision_id: str | None,
    quote: RFQOffer | None,
) -> str | None:
    if decision_id is None:
        return None
    decision = next(
        (
            item
            for item in state.decision_index
            if isinstance(item, MobilisationDecision) and item.decision_id == decision_id
        ),
        None,
    )
    if decision is None:
        return "unknown_decision"
    if decision.mission_id != mission_id:
        return "revision_conflict"
    evaluation = next(
        (item for item in decision.evaluations if item.selected and item.ship_id == ship_id),
        None,
    )
    if evaluation is None:
        return "revision_conflict"
    if revision_id is not None and evaluation.revision.revision_id != revision_id:
        return "revision_conflict"
    if requested_seats > evaluation.proposed_seats:
        return "revision_conflict"
    if quote is not None and (
        evaluation.quote is None
        or evaluation.quote.offer_id != quote.offer_id
        or requested_seats != evaluation.proposed_seats
    ):
        return "revision_conflict"
    return None


def _append_command(state: RunState, command_id: str, operation: str, payload, value):
    return replace(
        state,
        command_index=(
            *state.command_index,
            (state.application_run_id, command_id, operation, payload, value),
        ),
    )


def _create_request(
    central: RescueCentral,
    state: RunState,
    *,
    command_id: str,
    mission_id: str,
    ship_id: str,
    requested_seats: int,
    revision_id: str,
    now,
    response_deadline,
    decision_id: str | None,
    quote: RFQOffer | None = None,
) -> tuple[RunState, Result]:
    try:
        command_id = normalize_id(command_id)
        mission_id = normalize_id(mission_id)
        ship_id = normalize_id(ship_id)
        requested_seats = normalize_positive_quantity(requested_seats)
        revision_id = normalize_id(revision_id) if revision_id is not None else None
        instant = normalize_instant(now)
        deadline = None if response_deadline is None else normalize_instant(response_deadline)
        decision_id = None if decision_id is None else normalize_id(decision_id)
        payload = (
            mission_id,
            ship_id,
            requested_seats,
            None if quote is None else quote.offer_id,
            revision_id,
            decision_id,
            deadline,
        )
        existing_command = _command_entry(state, command_id)
        if existing_command is not None:
            if existing_command[2] == "create_request" and existing_command[3] == payload:
                return state, _result("replayed", existing_command[4])
            return state, _result("rejected", reason="identity_conflict")

        mission = _mission(state, mission_id)
        if mission is None:
            return state, _result("rejected", reason="unknown_mission")
        decision_reason = _decision_link_reason(
            state,
            decision_id,
            mission_id,
            ship_id,
            requested_seats,
            revision_id,
            quote,
        )
        if decision_reason is not None:
            return state, _result("rejected", reason=decision_reason)
        if quote is None:
            if revision_id is None:
                return state, _result("rejected", reason="revision_conflict")
            capacity_reason = _request_capacity_reason(
                state, mission, ship_id, requested_seats, revision_id
            )
            if capacity_reason is not None:
                return state, _result("rejected", reason=capacity_reason)
        else:
            rfq = _find_rfq(state, quote.rfq_id)
            if rfq is None or rfq.mission_id != mission_id or rfq.ship_id != ship_id:
                return state, _result("rejected", reason="identity_conflict")
            if quote.status != "held":
                return state, _result(
                    "rejected",
                    reason="expired_quote" if quote.status == "expired" else "identity_conflict",
                )
            if quote.expires_at <= instant:
                return state, _result("rejected", reason="expired_quote")
            if requested_seats != quote.offered_seats:
                return state, _result("rejected", reason="identity_conflict")
            if (
                revision_id is not None
                and _offer_revision(state, mission_id, ship_id, revision_id) is None
            ):
                return state, _result("rejected", reason="revision_conflict")
        if deadline is not None and deadline <= instant:
            return state, _result("rejected", reason="invalid_input")

        request = SeatRequest(
            request_id=central.id_source.next_id("request"),
            command_id=command_id,
            mission_id=mission_id,
            ship_id=ship_id,
            requested_seats=requested_seats,
            confirmed_seats=0,
            outcome="pending",
            submitted_at=instant,
            response_deadline=deadline,
            quote_id=None if quote is None else quote.offer_id,
            revision_id=revision_id,
            decision_id=decision_id,
        )
        context = TransitionContext(
            event_id=central.id_source.next_id("event"),
            at=instant,
            reason="quote_accepted" if quote is not None else "request_created",
        )
        updated_mission = mission_rules.add_request(mission, request, context)
        updated_state = _set_mission(state, updated_mission)
        if quote is not None:
            updated_market = market_rules.transfer_quote(
                updated_state.market, quote.offer_id, request.request_id, instant
            )
            updated_state = replace(updated_state, market=updated_market)
        updated_state = _append_command(
            updated_state, command_id, "create_request", payload, request
        )
        return updated_state, _result("applied", request)
    except (DomainValidationError, TypeError) as error:
        return state, _result("rejected", reason=_reason(error))


@dataclass(frozen=True, slots=True)
class RescueCentral:
    application_run_id: str
    central_id: str
    store: TransactionStore
    clock: Clock
    id_source: IdSource

    def register_mission(self, command: RegisterMission) -> Result[MissionSnapshot]:
        def operation(state: RunState):
            try:
                mission = mission_rules.register(
                    MissionData(
                        command.mission_id,
                        command.station_name,
                        command.people_count,
                        command.created_at,
                    )
                )
                if _mission(state, mission.mission_id) is not None:
                    return state, _result("rejected", reason="identity_conflict")
                return replace(state, missions=(*state.missions, mission)), _result(
                    "applied", mission
                )
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def register_ship(self, command: RegisterShip) -> Result[ShipSnapshot]:
        def operation(state: RunState):
            try:
                ship = Ship(command.ship_id, command.name)
                if any(item.ship_id == ship.ship_id for item in state.market.ships):
                    return state, _result("rejected", reason="identity_conflict")
                market = replace(state.market, ships=(*state.market.ships, ship))
                return replace(state, market=market), _result("applied", ship)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def publish_availability(self, command: PublishAvailability) -> Result[AvailabilitySnapshot]:
        def operation(state: RunState):
            try:
                if not isinstance(command.availability, ShipAvailability):
                    raise DomainValidationError("availability must be a ShipAvailability value")
                market = market_rules.publish_availability(state.market, command.availability)
                if market == state.market:
                    status = "replayed"
                else:
                    status = "applied"
                return replace(state, market=market), _result(status, command.availability)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def publish_offer(self, command: PublishOffer) -> Result[OfferSnapshot]:
        def operation(state: RunState):
            try:
                mission_id = normalize_id(command.mission_id)
                ship_id = normalize_id(command.ship_id)
                offer_id = normalize_id(command.offer_id)
                if _mission(state, mission_id) is None:
                    return state, _result("rejected", reason="unknown_mission")
                if not any(item.ship_id == ship_id for item in state.market.ships):
                    return state, _result("rejected", reason="unknown_ship")
                revision = command.revision
                if not isinstance(revision, ShipOfferRevision):
                    raise DomainValidationError("revision must be a ShipOfferRevision")
                existing_offer = next(
                    (item for item in state.market.offers if item.offer_id == offer_id),
                    None,
                )
                if existing_offer is not None and (
                    existing_offer.mission_id != mission_id or existing_offer.ship_id != ship_id
                ):
                    return state, _result("rejected", reason="identity_conflict")
                for offer in state.market.offers:
                    for existing in offer.revisions:
                        if existing.revision_id == revision.revision_id:
                            if offer.offer_id == offer_id and existing == revision:
                                return state, _result("replayed", offer)
                            return state, _result("rejected", reason="revision_conflict")
                market = market_rules.publish_offer_revision(
                    state.market,
                    offer_id,
                    revision,
                    mission_id=mission_id,
                    ship_id=ship_id,
                )
                snapshot = next(item for item in market.offers if item.offer_id == offer_id)
                return replace(state, market=market), _result("applied", snapshot)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def request_quotes(self, command: RequestQuotes) -> Result[tuple[RFQSnapshot, ...]]:
        def operation(state: RunState):
            try:
                mission = _mission(state, command.mission_id)
                if mission is None:
                    return state, _result("rejected", reason="unknown_mission")
                now = normalize_instant(command.now)
                deadline = (
                    None
                    if command.response_deadline is None
                    else normalize_instant(command.response_deadline)
                )
                if deadline is not None and deadline <= now:
                    return state, _result("rejected", reason="invalid_input")
                outstanding = mission_rules.progress(mission).additional_needed
                if outstanding == 0:
                    return state, _result("applied", ())
                market = state.market
                created: list[SeatRFQ] = []
                for ship in sorted(market.ships, key=lambda item: item.ship_id):
                    latest = market_rules.latest_availability(market, ship.ship_id)
                    if latest is None or not latest.available:
                        continue
                    inventory = market_rules.usage(market, state.missions, ship.ship_id)
                    if inventory.shortfall or inventory.free == 0:
                        continue
                    requested_seats = min(outstanding, inventory.free)
                    if requested_seats <= 0:
                        continue
                    rfq = SeatRFQ(
                        rfq_id=self.id_source.next_id("rfq"),
                        mission_id=mission.mission_id,
                        ship_id=ship.ship_id,
                        availability_id=latest.availability_id,
                        requested_seats=requested_seats,
                        status="pending",
                        sent_at=now,
                        response_deadline=deadline,
                    )
                    created.append(rfq)
                if not created:
                    return state, _result("applied", ())
                market = replace(market, rfqs=(*market.rfqs, *created))
                return replace(state, market=market), _result("applied", tuple(created))
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def record_quote(self, command: RecordQuote) -> Result[QuoteSnapshot]:
        def operation(state: RunState):
            try:
                quote = command.offer
                if not isinstance(quote, RFQOffer):
                    raise DomainValidationError("offer must be an RFQOffer")
                rfq = _find_rfq(state, quote.rfq_id)
                if rfq is None:
                    return state, _result("rejected", reason="invalid_input")
                now = normalize_instant(command.now)
                market = market_rules.hold_quote(state.market, state.missions, quote, now)
                return replace(state, market=market), _result("applied", quote)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def accept_quote(self, command: AcceptQuote) -> Result[RequestSnapshot]:
        def operation(state: RunState):
            try:
                command_id = normalize_id(command.command_id)
                mission_id = normalize_id(command.mission_id)
                quote_id = normalize_id(command.quote_id)
                quote = _find_quote(state, quote_id)
                payload_quote = quote_id
                payload = (
                    mission_id,
                    payload_quote,
                    None
                    if command.response_deadline is None
                    else normalize_instant(command.response_deadline),
                    None if command.decision_id is None else normalize_id(command.decision_id),
                    None if command.revision_id is None else normalize_id(command.revision_id),
                )
                existing = _command_entry(state, command_id)
                if existing is not None:
                    if existing[2] == "accept_quote" and existing[3] == payload:
                        return state, _result("replayed", existing[4])
                    return state, _result("rejected", reason="identity_conflict")
                if quote is None:
                    return state, _result("rejected", reason="expired_quote")
                rfq = _find_rfq(state, quote.rfq_id)
                if rfq is None or rfq.mission_id != mission_id:
                    return state, _result("rejected", reason="identity_conflict")
                if quote.expires_at <= normalize_instant(command.now):
                    expired_market = market_rules.close_quote(
                        state.market, quote_id, "expired", command.now
                    )
                    return replace(state, market=expired_market), _result(
                        "rejected", reason="expired_quote"
                    )
                result_state, result = _create_request(
                    self,
                    state,
                    command_id=command_id,
                    mission_id=mission_id,
                    ship_id=rfq.ship_id,
                    requested_seats=quote.offered_seats,
                    revision_id=command.revision_id,
                    now=command.now,
                    response_deadline=command.response_deadline,
                    decision_id=command.decision_id,
                    quote=quote,
                )
                if result.status == "applied":
                    result_state = replace(
                        result_state,
                        command_index=tuple(
                            (item[0], item[1], "accept_quote", payload, item[4])
                            if isinstance(item, tuple) and len(item) == 5 and item[1] == command_id
                            else item
                            for item in result_state.command_index
                        ),
                    )
                return result_state, result
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def create_request(self, command: CreateRequest) -> Result[RequestSnapshot]:
        return self.store.transact(
            lambda state: _create_request(
                self,
                state,
                command_id=command.command_id,
                mission_id=command.mission_id,
                ship_id=command.ship_id,
                requested_seats=command.requested_seats,
                revision_id=command.revision_id,
                now=command.now,
                response_deadline=command.response_deadline,
                decision_id=command.decision_id,
            )
        )

    def reject_quote(self, command: RejectQuote) -> Result[QuoteSnapshot]:
        def operation(state: RunState):
            try:
                quote_id = normalize_id(command.quote_id)
                quote = _find_quote(state, quote_id)
                if quote is None:
                    return state, _result("rejected", reason="expired_quote")
                if quote.status != "held":
                    return state, _result("rejected", reason="closed_request")
                market = market_rules.close_quote(state.market, quote_id, "rejected", command.now)
                closed = _find_quote(replace(state, market=market), quote_id)
                return replace(state, market=market), _result("applied", closed)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def expire_quotes(self, now) -> Result[tuple[str, ...]]:
        def operation(state: RunState):
            try:
                instant = normalize_instant(now)
                market = state.market
                expired_ids: list[str] = []
                for quote in tuple(market.quotes):
                    if quote.status == "held" and quote.expires_at <= instant:
                        market = market_rules.close_quote(
                            market, quote.offer_id, "expired", instant
                        )
                        expired_ids.append(quote.offer_id)
                updated_rfqs = []
                for rfq in market.rfqs:
                    if (
                        rfq.status == "pending"
                        and rfq.response_deadline is not None
                        and rfq.response_deadline <= instant
                    ):
                        updated_rfqs.append(replace(rfq, status="expired"))
                        expired_ids.append(rfq.rfq_id)
                    else:
                        updated_rfqs.append(rfq)
                market = replace(market, rfqs=tuple(updated_rfqs))
                return replace(state, market=market), _result("applied", tuple(expired_ids))
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def cancel_request(self, command: CancelRequest) -> Result[RequestSnapshot]:
        return self._close_request(
            command.mission_id, command.request_id, command.now, "cancelled", command.reason
        )

    def expire_request(self, command: ExpireRequest) -> Result[RequestSnapshot]:
        def operation(state: RunState):
            mission = _mission(state, command.mission_id)
            if mission is None:
                return state, _result("rejected", reason="unknown_mission")
            request = next(
                (item for item in mission.requests if item.request_id == command.request_id), None
            )
            if request is None:
                return state, _result("rejected", reason="unknown_request")
            if request.outcome != "pending":
                return state, _result("ignored", request, "closed_request")
            try:
                instant = normalize_instant(command.now)
                if request.response_deadline is None or instant < request.response_deadline:
                    return state, _result("rejected", reason="invalid_input")
                updated = mission_rules.apply_outcome(
                    mission,
                    request.request_id,
                    "expired",
                    0,
                    TransitionContext(self.id_source.next_id("event"), instant, "request_expired"),
                )
                updated_state = _set_mission(state, updated)
                return updated_state, _result(
                    "applied",
                    next(
                        item for item in updated.requests if item.request_id == request.request_id
                    ),
                )
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def _close_request(self, mission_id: str, request_id: str, now, outcome: str, reason: str):
        def operation(state: RunState):
            mission = _mission(state, mission_id)
            if mission is None:
                return state, _result("rejected", reason="unknown_mission")
            request = next(
                (item for item in mission.requests if item.request_id == request_id), None
            )
            if request is None:
                return state, _result("rejected", reason="unknown_request")
            if request.outcome != "pending":
                return state, _result("ignored", request, "closed_request")
            try:
                updated = mission_rules.apply_outcome(
                    mission,
                    request_id,
                    outcome,
                    0,
                    TransitionContext(
                        self.id_source.next_id("event"),
                        normalize_instant(now),
                        reason,
                    ),
                )
                updated_state = _set_mission(state, updated)
                result_request = next(
                    item for item in updated.requests if item.request_id == request_id
                )
                return updated_state, _result("applied", result_request)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def record_response(self, command: RecordResponse) -> Result[RequestSnapshot]:
        def operation(state: RunState):
            try:
                message_id = normalize_id(command.message_id)
                request_id = normalize_id(command.request_id)
                delivery_id = normalize_id(command.delivery_id)
                attempt = normalize_positive_quantity(command.attempt_number)
                sent_at = normalize_instant(command.sent_at)
                received_at = (
                    None if command.received_at is None else normalize_instant(command.received_at)
                )
                communication_rtt = (
                    None
                    if command.communication_rtt_seconds is None
                    else normalize_instant(command.communication_rtt_seconds)
                )
                confirmed = normalize_nonnegative_quantity(command.confirmed_seats)
                if received_at is not None and received_at < sent_at:
                    raise DomainValidationError("receipt cannot precede send time")
                message = CommunicationMessage(
                    message_id=message_id,
                    correlation_id=request_id,
                    request_id=request_id,
                    kind="ship_response",
                    payload=(("outcome", command.outcome), ("confirmed_seats", confirmed)),
                    sent_at=sent_at,
                )
                known_delivery = next(
                    (
                        item
                        for item in state.delivery_index
                        if isinstance(item, tuple) and len(item) == 3 and item[0] == delivery_id
                    ),
                    None,
                )
                existing_message = next(
                    (
                        item
                        for item in state.message_index
                        if isinstance(item, tuple)
                        and len(item) == 2
                        and item[0].message_id == message_id
                    ),
                    None,
                )
                if known_delivery is not None:
                    existing = known_delivery[2]
                    same_message = existing_message is not None and existing_message[0] == message
                    if (
                        known_delivery[1] == message_id
                        and same_message
                        and existing.attempt_number == attempt
                        and existing.received_at == received_at
                        and existing.communication_rtt_seconds == communication_rtt
                    ):
                        return state, _result("ignored")
                    return state, _result("rejected", reason="identity_conflict")

                def publish_delivery(
                    target_state: RunState,
                    disposition: str,
                    delivery_reason: str,
                    *,
                    keep_message: bool = True,
                ):
                    delivery = MessageDelivery(
                        delivery_id=delivery_id,
                        attempt_number=attempt,
                        received_at=received_at,
                        disposition=disposition,
                        reason=delivery_reason,
                        communication_rtt_seconds=(
                            None if received_at is None else communication_rtt
                        ),
                    )
                    messages = target_state.message_index
                    if keep_message:
                        if existing_message is None:
                            messages = (*messages, (message, (delivery,)))
                        else:
                            messages = tuple(
                                (item[0], (*item[1], delivery))
                                if item is existing_message
                                else item
                                for item in messages
                            )
                    updated = replace(
                        target_state,
                        message_index=messages,
                        delivery_index=(
                            *target_state.delivery_index,
                            (delivery_id, message_id, delivery),
                        ),
                    )
                    return updated

                if existing_message is not None and existing_message[0] != message:
                    updated = publish_delivery(
                        state, "rejected", "identity_conflict", keep_message=False
                    )
                    return updated, _result("rejected", reason="identity_conflict")

                mission = next(
                    (
                        candidate
                        for candidate in state.missions
                        if any(item.request_id == request_id for item in candidate.requests)
                    ),
                    None,
                )
                if mission is None:
                    if received_at is None:
                        return publish_delivery(state, "lost", "transport_loss"), _result("applied")
                    return publish_delivery(state, "ignored", "unknown_request"), _result(
                        "ignored", reason="unknown_request"
                    )
                request = next(item for item in mission.requests if item.request_id == request_id)
                if sent_at < request.submitted_at:
                    return publish_delivery(state, "rejected", "invalid_input"), _result(
                        "rejected", reason="invalid_input"
                    )
                if received_at is None:
                    return publish_delivery(state, "lost", "transport_loss"), _result(
                        "applied", request
                    )
                if request.outcome != "pending":
                    if (
                        request.outcome == "expired"
                        and request.response_deadline is not None
                        and received_at >= request.response_deadline
                    ):
                        return publish_delivery(state, "late", "deadline_expired"), _result(
                            "ignored", request, "late"
                        )
                    return publish_delivery(state, "ignored", "closed_request"), _result(
                        "ignored", request, "closed_request"
                    )
                if (
                    request.response_deadline is not None
                    and received_at >= request.response_deadline
                ):
                    expired = mission_rules.apply_outcome(
                        mission,
                        request_id,
                        "expired",
                        0,
                        TransitionContext(
                            self.id_source.next_id("event"),
                            received_at,
                            "response_deadline_reached",
                            message_id,
                        ),
                    )
                    updated = _set_mission(state, expired)
                    result_request = next(
                        item for item in expired.requests if item.request_id == request_id
                    )
                    updated = publish_delivery(updated, "late", "deadline_expired")
                    return updated, _result("ignored", result_request, "late")
                try:
                    updated_mission = mission_rules.apply_outcome(
                        mission,
                        request_id,
                        command.outcome,
                        confirmed,
                        TransitionContext(
                            self.id_source.next_id("event"),
                            received_at,
                            command.outcome,
                            message_id,
                        ),
                    )
                except (DomainValidationError, TypeError) as error:
                    reason = _reason(error)
                    return publish_delivery(state, "rejected", reason), _result(
                        "rejected", reason=reason
                    )
                updated = _set_mission(state, updated_mission)
                result_request = next(
                    item for item in updated_mission.requests if item.request_id == request_id
                )
                updated = publish_delivery(updated, "applied", "response_applied")
                return updated, _result("applied", result_request)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def get_progress(self, mission_id: str, now) -> Result[MissionProgress]:
        def operation(state: RunState):
            try:
                normalize_instant(now)
                mission = _mission(state, mission_id)
                if mission is None:
                    return state, _result("rejected", reason="unknown_mission")
                return state, _result("applied", mission_rules.progress(mission))
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def get_history(self, mission_id: str) -> Result[tuple[RequestHistoryEntry, ...]]:
        def operation(state: RunState):
            try:
                mission = _mission(state, mission_id)
                if mission is None:
                    return state, _result("rejected", reason="unknown_mission")
                return state, _result("applied", mission.history)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def get_decision(self, decision_id: str) -> Result[DecisionSnapshot]:
        def operation(state: RunState):
            try:
                normalized = normalize_id(decision_id)
                decision = next(
                    (
                        item
                        for item in state.decision_index
                        if isinstance(item, MobilisationDecision) and item.decision_id == normalized
                    ),
                    None,
                )
                if decision is None:
                    return state, _result("rejected", reason="unknown_decision")
                return state, _result("applied", decision)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def get_deliveries(self, message_id: str) -> Result[tuple[MessageDelivery, ...]]:
        def operation(state: RunState):
            try:
                normalized = normalize_id(message_id)
                deliveries = tuple(
                    item[2]
                    for item in state.delivery_index
                    if isinstance(item, tuple) and len(item) == 3 and item[1] == normalized
                )
                if not deliveries:
                    return state, _result("rejected", reason="unknown_message")
                return state, _result("applied", deliveries)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)

    def compare(self, command: ComparePolicies) -> Result[tuple[RunSnapshot, ...]]:
        """Run configured policies against one immutable scenario revision."""
        try:
            if not isinstance(command, ComparePolicies):
                raise DomainValidationError("compare requires a ComparePolicies command")
            scenario_id = normalize_id(command.scenario_id)
            scenario_revision = normalize_positive_quantity(command.scenario_revision)
            if not isinstance(command.policy_keys, (tuple, list)) or not command.policy_keys:
                raise DomainValidationError("comparison requires at least one policy key")

            policy_keys: list[tuple[str, int]] = []
            for key in command.policy_keys:
                if not isinstance(key, (tuple, list)) or len(key) != 2:
                    raise DomainValidationError("policy keys require an ID and revision")
                normalized_key = (
                    normalize_id(key[0]),
                    normalize_positive_quantity(key[1]),
                )
                if normalized_key in policy_keys:
                    raise DomainValidationError("policy keys must be unique")
                policy_keys.append(normalized_key)

            # Capture scenario and policies together, then release the operational store
            # lock before any scenario processing begins.
            state = self.store.snapshot()
            scenario = next(
                (
                    item
                    for item in state.scenarios
                    if item.scenario_id == scenario_id and item.revision == scenario_revision
                ),
                None,
            )
            if scenario is None:
                raise DomainValidationError("unknown scenario revision")

            policies = []
            for policy_id, revision in policy_keys:
                policy = next(
                    (
                        item
                        for item in state.policies
                        if item.policy_id == policy_id and item.revision == revision
                    ),
                    None,
                )
                if policy is None:
                    raise DomainValidationError("unknown policy revision")
                policies.append(policy)
        except DomainValidationError, TypeError:
            return _result("rejected", reason="invalid_input")

        from rescue.experiments.runner import simulate

        try:
            snapshots = tuple(
                simulate(scenario, policy, self.id_source.next_id("simulation"))
                for policy in policies
            )
        except DomainValidationError, TypeError:
            return _result("rejected", reason="invalid_input")
        return _result("applied", snapshots)

    def mobilise(self, command: Mobilise) -> Result[DecisionSnapshot]:
        def operation(state: RunState):
            try:
                mission_id = normalize_id(command.mission_id)
                policy_id = normalize_id(command.policy_id)
                policy_revision = normalize_positive_quantity(command.policy_revision)
                instant = normalize_instant(command.now)
                mission = _mission(state, mission_id)
                if mission is None:
                    return state, _result("rejected", reason="unknown_mission")
                policy = next(
                    (
                        value
                        for value in state.policies
                        if isinstance(value, MobilisationPolicy)
                        and value.policy_id == policy_id
                        and value.revision == policy_revision
                    ),
                    None,
                )
                if policy is None:
                    return state, _result("rejected", reason="invalid_input")

                offers = tuple(
                    offer for offer in state.market.offers if offer.mission_id == mission_id
                )
                candidates: list[Candidate] = []
                for offer in sorted(offers, key=lambda item: item.ship_id):
                    revision = offer.current_revision
                    inventory = market_rules.usage(state.market, state.missions, offer.ship_id)
                    revision_used = sum(
                        request.requested_seats
                        if request.outcome == "pending"
                        else request.confirmed_seats
                        for current_mission in state.missions
                        for request in current_mission.requests
                        if request.revision_id == revision.revision_id
                        and request.outcome in {"pending", "accepted", "partially_accepted"}
                    )
                    free_for_revision = max(0, revision.capacity - revision_used)
                    candidates.append(
                        Candidate(
                            revision=revision,
                            free_seats=min(inventory.free, free_for_revision),
                            ship_id=offer.ship_id,
                        )
                    )
                decision = select_offers(
                    mission,
                    tuple(candidates),
                    policy,
                    DecisionContext(
                        decision_id=self.id_source.next_id("decision"),
                        recorded_at=instant,
                        evaluation_ids=tuple(
                            self.id_source.next_id("evaluation") for _ in candidates
                        ),
                    ),
                )
                updated_state = replace(
                    state,
                    decision_index=(*state.decision_index, decision),
                )
                return updated_state, _result("applied", decision)
            except (DomainValidationError, TypeError) as error:
                return state, _result("rejected", reason=_reason(error))

        return self.store.transact(operation)
