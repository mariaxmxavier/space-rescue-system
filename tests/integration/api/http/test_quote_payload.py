"""Exercise nested quote decoding on the real HTTP boundary for browser workflows."""

from fastapi.testclient import TestClient

from rescue.api.app import create_app


def test_nested_quote_payload_reaches_the_application_and_rejects_unknown_fields():
    """Resolve trusted quote annotations without changing application rejection rules."""
    with TestClient(create_app()) as client:
        client.post("/runs", json={"application_run_id": "quote-codec", "central_id": "central"})
        offer = {
            "offer_id": "quote",
            "rfq_id": "unknown-rfq",
            "offered_seats": 2,
            "arrival_estimate_seconds": "1.125",
            "expires_at": "10",
            "recorded_at": "0",
        }
        response = client.post(
            "/runs/quote-codec/operations/record_quote",
            json={"command": {"offer": offer, "now": "0"}},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        assert response.json()["reason"]
        before = client.get("/runs/quote-codec/state").json()
        malformed = client.post(
            "/runs/quote-codec/operations/record_quote",
            json={"command": {"offer": {**offer, "invented": True}, "now": "0"}},
        )
        assert malformed.status_code == 400
        assert "unknown fields" in malformed.json()["detail"]
        assert client.get("/runs/quote-codec/state").json() == before
