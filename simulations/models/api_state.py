"""Typed read-only bundle of request and communication projections."""

from simulations.models.base import StrictModel
from simulations.models.delivery_view import DeliveryView
from simulations.models.request_view import RequestView
from simulations.models.session_view import SessionView


class ApiState(StrictModel):
    """Return only structured request, session and delivery views from a state read."""

    requests: tuple[RequestView, ...] = ()
    sessions: tuple[SessionView, ...] = ()
    deliveries: tuple[DeliveryView, ...] = ()
