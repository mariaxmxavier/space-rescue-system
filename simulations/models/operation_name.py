"""Supported mission API operation names."""

from enum import StrEnum


class OperationName(StrEnum):
    """Identify an API operation in an invocation and its outcome."""

    CREATE_RUN = "create_run"
    REGISTER_MISSION = "register_mission"
    REGISTER_SHIP = "register_ship"
    PUBLISH_AVAILABILITY = "publish_availability"
    PUBLISH_OFFER = "publish_offer"
    MOBILISE = "mobilise"
    CREATE_REQUEST = "create_request"
    RECORD_RESPONSE = "record_response"
    CANCEL_REQUEST = "cancel_request"
    EXPIRE_REQUEST = "expire_request"
    GET_PROGRESS = "get_progress"
    GET_SESSION = "get_session"
    GET_DELIVERIES = "get_deliveries"
