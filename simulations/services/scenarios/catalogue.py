"""Compose four bounded one-mission cases from reusable typed situation recipes."""

from decimal import Decimal

from simulations.models.close_kind import CloseKind
from simulations.models.close_request import CloseRequest
from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.event_phase import EventPhase
from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.final_expectation import FinalExpectation
from simulations.models.fleet_update import FleetUpdate
from simulations.models.mission_setup import MissionSetup
from simulations.models.observe import Observe
from simulations.models.publish_fleet import PublishFleet
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.scenario_profile import ScenarioProfile
from simulations.models.ship_reply import ShipReply
from simulations.models.ship_setup import ShipSetup
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe
from simulations.models.solver_round import SolverRound
from simulations.models.timeline_event import TimelineEvent

CASE_IDS = ("baseline", "all10", "all11", "all12")


def profile(case_id):
    """Build an immutable validated profile, failing unknown names before HTTP side effects."""
    if case_id not in CASE_IDS:
        raise ValueError(f"Unknown simulation case: {case_id}")
    events = []
    recipes = []

    def add(time, label, action, situation=None, check=None, expected=None):
        if isinstance(action, SolverRound):
            action = action.model_copy(
                update={
                    "response_deadline": Decimal("10")
                    if time == 0
                    else (Decimal("20") if time < 20 else Decimal("40"))
                }
            )
        phase = (
            EventPhase.SOLVER_ROUND
            if isinstance(action, (SolverRound, ConcurrentRequests))
            else (
                EventPhase.FLEET_CHANGE
                if isinstance(action, PublishFleet)
                else (
                    EventPhase.CLOSURE if isinstance(action, CloseRequest) else EventPhase.DELIVERY
                )
            )
        )
        events.append(
            TimelineEvent(
                event_id=label,
                time=Decimal(str(time)),
                phase=phase,
                ordinal=len(events),
                action=action,
                situation_ids=() if situation is None else (situation,),
            )
        )
        if situation is not None and not any(
            recipe.situation_id == situation for recipe in recipes
        ):
            recipes.append(
                SituationRecipe(
                    situation_id=situation,
                    trigger=label,
                    action=action,
                    evidence=EvidencePredicate(check_name=check, expected=expected),
                )
            )

    def reply(ship, occurrence, seats, label, *, partial=False, **kwargs):
        return ShipReply(
            request=RequestSelector(ship_key=ship, occurrence=occurrence),
            reply=ReplyKind.REFUSE
            if seats is None
            else (ReplyKind.PARTIAL if partial else ReplyKind.CONFIRM),
            seats=seats,
            message_label=label,
            **kwargs,
        )

    add(0, "Initial solver selects A4 B4 C2", SolverRound(response_deadline=Decimal("10")))
    add(
        1,
        "A confirms all four seats",
        reply("A", 1, 4, "a-full"),
        SituationId.FULL_CONFIRMATION,
        "application_status",
        "applied",
    )
    if case_id == "baseline":
        add(2, "B confirms all four seats", reply("B", 1, 4, "b-full"))
        add(3, "C confirms both seats", reply("C", 1, 2, "c-full"))
    else:
        add(2, "B partially confirms two of four", reply("B", 1, 2, "b-partial", partial=True))
        add(
            2,
            "C refuses its initial request",
            reply("C", 1, None, "c-refuse"),
            SituationId.PARTIAL_AND_REFUSAL,
            "partial_and_refusal",
            True,
        )
        add(
            2,
            "Solver proposes replacement; submission deferred",
            SolverRound(response_deadline=Decimal("20"), submit=False),
        )
        add(
            3,
            "B capacity falls to two and C becomes unavailable",
            PublishFleet(
                updates=(
                    FleetUpdate(ship_key="B", capacity=2),
                    FleetUpdate(ship_key="C", available=False),
                )
            ),
            SituationId.AVAILABILITY_CHANGE,
            "confirmed",
            6,
        )
        add(
            3,
            "Solver records four-seat capacity shortfall",
            SolverRound(response_deadline=Decimal("20"), submit=False),
            SituationId.INSUFFICIENT_CAPACITY,
            "shortfall",
            4,
        )
        add(
            4,
            "B and C availability restored",
            PublishFleet(
                updates=(
                    FleetUpdate(ship_key="B", capacity=4),
                    FleetUpdate(ship_key="C", available=True),
                )
            ),
        )
        add(
            4,
            "Solver submits B2 C2 replacement requests",
            SolverRound(response_deadline=Decimal("10")),
        )
        add(
            5,
            "Cancel B replacement request",
            CloseRequest(
                request=RequestSelector(ship_key="B", occurrence=2), close_as=CloseKind.CANCEL
            ),
            SituationId.CANCELLATION,
            "application_status",
            "applied",
        )
        add(
            5,
            "Solver proposes B2; submission deferred",
            SolverRound(response_deadline=Decimal("20"), submit=False),
        )
        add(
            6,
            "B replies to cancelled request",
            reply("B", 2, 2, "b-closed"),
            SituationId.CLOSED_REQUEST_RESPONSE,
            "reason",
            "closed_request",
        )
        add(
            12,
            "C sends sequence two; delivery held until after deadline",
            Observe(reason="send only; no receipt is claimed"),
        )
        add(
            20,
            "Expire C replacement at its deadline",
            CloseRequest(
                request=RequestSelector(ship_key="C", occurrence=2), close_as=CloseKind.EXPIRE
            ),
            SituationId.EXPIRATION,
            "application_status",
            "applied",
        )
        add(
            20,
            "Solver proposes B2 C2; submission deferred",
            SolverRound(response_deadline=Decimal("20"), submit=False),
        )
        add(
            21,
            "C retry sequence three arrives after deadline",
            reply("C", 2, 2, "c-late", sent_at=Decimal("12"), sequence=3, delivery_attempt=2),
            SituationId.DELAYED_RESPONSE,
            "reason",
            "late",
        )
        add(
            22,
            "C original sequence two arrives after sequence three",
            reply("C", 2, 2, "c-original", sent_at=Decimal("12"), sequence=2),
            SituationId.OUT_OF_ORDER,
            "session_gap_and_obsolete_sequence",
            ("gap", "duplicate_sequence"),
        )
        if case_id == "all12":
            add(
                23,
                "Two clients compete for solver-selected B2; submit C2 once",
                ConcurrentRequests(ship_key="B"),
                SituationId.SIMULTANEOUS_OPERATIONS,
                "concurrent_outcomes",
                ("applied", "insufficient_capacity"),
            )
        else:
            add(
                23,
                "Solver submits fresh final B2 C2 requests",
                SolverRound(response_deadline=Decimal("10")),
            )
        add(
            24,
            "C incorrectly confirms three seats on two-seat request",
            reply("C", 3, 3, "c-invalid"),
            SituationId.INVALID_QUANTITY,
            "reason",
            "invalid_input",
        )
        add(25, "C corrects response and confirms two seats", reply("C", 3, 2, "c-final"))
        add(25, "B confirms final two seats; mission completes", reply("B", 3, 2, "b-final"))
        if case_id in {"all11", "all12"}:
            add(
                26,
                "Replay accepted C response without adding seats",
                reply("C", 3, 2, "c-replay", replay_of="c-final", delivery_attempt=2),
                SituationId.DUPLICATE_RESPONSE,
                "message_replay",
                True,
            )
    included = tuple(recipe.situation_id for recipe in recipes)
    return ScenarioProfile(
        scenario_id=case_id,
        mission=MissionSetup(station_name="Aurora", demand=10),
        ships=tuple(
            ShipSetup(
                ship_key=key,
                name=f"Rescue {key}",
                capacity=capacity,
                arrival=Decimal(arrival),
                offer_revision=1,
            )
            for key, capacity, arrival in (("A", 4, "1"), ("B", 4, "2"), ("C", 2, "3"))
        ),
        recipes=tuple(recipes),
        included_situations=included,
        events=tuple(events),
        expectation=FinalExpectation(
            mission_status="complete",
            confirmed=10,
            pending=0,
            unconfirmed=0,
            required_situations=included,
        ),
    )
