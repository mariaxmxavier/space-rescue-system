"""Schedule additional high-demand missions on the same fleet and run."""

from decimal import Decimal

from simulations.models.mission_setup import MissionSetup
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName
from simulations.models.response_outcome import ResponseOutcome
from simulations.models.session_direction import SessionDirection
from simulations.models.session_envelope import SessionEnvelope
from simulations.models.ship_setup import ShipSetup
from simulations.services.solver_round import solver_round


def schedule_missions(api, namespace, policy, capture):
    """Return a hook that inserts arrivals and responses at their declared virtual times."""
    queue = [
        (Decimal(t), kind, n)
        for n, t in enumerate((2, 8, 16), 1)
        for kind, t in (("arrival", t), ("confirmation", t + 4))
    ]
    queue.sort()
    mission_ids = []
    requests = {}

    def invoke(command):
        outcome = api.invoke(namespace, command)
        if outcome.http_status != 200 or outcome.application_status != "applied":
            raise ValueError(f"Additional mission operation failed: {outcome.reason}")
        return outcome

    def before_event(event, run_id, primary_id):
        while queue and queue[0][0] <= event.time:
            now, kind, n = queue.pop(0)
            mission_id = f"{namespace}-surge-{n}"
            if kind == "arrival":
                invoke(
                    OperationCommand(
                        operation=OperationName.REGISTER_MISSION,
                        mission_id=mission_id,
                        mission=MissionSetup(station_name=f"Outpost {n}", demand=120),
                        at=now,
                    )
                )
                mission_ids.append(mission_id)
                for key, capacity, arrival in (("A", 4, "1"), ("B", 4, "2"), ("C", 2, "3")):
                    invoke(
                        OperationCommand(
                            operation=OperationName.PUBLISH_OFFER,
                            mission_id=mission_id,
                            ship_id=f"{namespace}-{key}",
                            offer_id=f"{mission_id}-{key}-offer",
                            revision_id=f"{mission_id}-{key}-revision",
                            revision_number=1,
                            offer_capacity=capacity,
                            arrival_estimate=Decimal(arrival),
                            available=True,
                            at=now,
                        )
                    )
                for ship in range(2):
                    ship_id = f"{mission_id}-ship-{ship}"
                    invoke(
                        OperationCommand(
                            operation=OperationName.REGISTER_SHIP,
                            ship_id=ship_id,
                            ship=ShipSetup(
                                ship_key=f"surge-{n}-{ship}",
                                name=f"Surge {n}-{ship + 1}",
                                capacity=60,
                                arrival=Decimal("0.1"),
                                offer_revision=1,
                            ),
                        )
                    )
                    invoke(
                        OperationCommand(
                            operation=OperationName.PUBLISH_AVAILABILITY,
                            availability_id=f"{ship_id}-availability",
                            ship_id=ship_id,
                            capacity=60,
                            arrival_estimate=Decimal("0.1"),
                            available=True,
                            at=now,
                        )
                    )
                    invoke(
                        OperationCommand(
                            operation=OperationName.PUBLISH_OFFER,
                            mission_id=mission_id,
                            ship_id=ship_id,
                            offer_id=f"{ship_id}-offer",
                            revision_id=f"{ship_id}-revision",
                            revision_number=1,
                            offer_capacity=60,
                            arrival_estimate=Decimal("0.1"),
                            available=True,
                            at=now,
                        )
                    )
                outcome = solver_round(
                    api, namespace, mission_id, policy, now, now + 30, mission_id
                )
                requests[n] = [item.value for item in outcome[1:]]
                capture(now, f"Outpost {n} arrives: 120 people need rescue", mission_ids)
            else:
                for index, request in enumerate(requests[n]):
                    invoke(
                        OperationCommand(
                            operation=OperationName.RECORD_RESPONSE,
                            request_id=request.request_id,
                            message_id=f"{mission_id}-message-{index}",
                            delivery_id=f"{mission_id}-delivery-{index}",
                            attempt_number=1,
                            outcome=ResponseOutcome.ACCEPTED,
                            confirmed_seats=request.requested_seats,
                            sent_at=now,
                            received_at=now,
                            envelope=SessionEnvelope(
                                session_id=f"local:{request.ship_id}",
                                version=1,
                                direction=SessionDirection.INBOUND,
                                sequence=1,
                            ),
                        )
                    )
                capture(now, f"Outpost {n}: rescue ships confirm 120 seats", mission_ids)

    return before_event, mission_ids
