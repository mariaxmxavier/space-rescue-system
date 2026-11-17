"""Exercise communication ordering and recovery through real browser controls.

When: an independent prepared mission has a sequenced request to answer.
Why: recovery, gaps and duplicates must not create repeated seat effects.
"""

from playwright.sync_api import Page, expect

from tests.e2e.web.support import choose, prepare_run, submit


def test_sequence_gaps_duplicates_and_recovery(live_workspace_page: Page):
    """Observe a genuine gap, repeated response, session synchronisation and report replay."""
    page = live_workspace_page
    invoke = prepare_run(page, "communication")
    response = invoke(
        "create_request",
        {
            "command_id": "request",
            "mission_id": "mission",
            "ship_id": "A",
            "requested_seats": 2,
            "revision_id": "revision",
            "now": "0",
            "response_deadline": "10",
        },
    )
    request_id = response["value"]["request_id"]
    session = {"session_id": "ship-A"}
    choose(page, "Communication")
    response = submit(
        page,
        "record_response",
        {
            "message_id": "answer",
            "delivery_id": "delivery",
            "attempt_number": 1,
            "request_id": request_id,
            "outcome": "accepted",
            "confirmed_seats": 2,
            "sent_at": "1",
            "received_at": "1",
            "include_envelope": True,
            "session_id": session["session_id"],
            "version": 1,
            "direction": "inbound",
            "sequence": 3,
        },
    )
    expect(response.locator(".result-summary")).to_contain_text("applied")
    duplicate = submit(
        page,
        "record_response",
        {"message_id": "answer", "delivery_id": "duplicate", "attempt_number": 2},
    )
    expect(duplicate.locator(".result-summary")).to_contain_text("ignored")
    inspection = submit(page, "get_session", {"session_id": session["session_id"]})
    inspection.get_by_text("Complete result", exact=True).click()
    expect(inspection.locator("pre")).to_contain_text('"gaps": [')
    expect(inspection.locator("pre")).to_contain_text('"next_inbound": 4')
    synchronised = submit(
        page,
        "synchronise_inbound",
        {"session_id": session["session_id"], "version": 1, "next_sequence": 5},
    )
    expect(synchronised.locator(".result-summary")).to_contain_text("applied")
    recovered = submit(
        page,
        "recover_reports",
        {"session_id": session["session_id"], "version": 1, "from_sequence": 1, "count": 1},
    )
    expect(recovered.locator(".result-summary")).to_contain_text("applied")
    deliveries = submit(page, "get_deliveries", {"message_id": "answer"})
    deliveries.get_by_text("Complete result", exact=True).click()
    expect(deliveries.locator("pre")).to_contain_text("duplicate")
    choose(page, "Missions")
    progress = submit(page, "get_progress", {"mission_id": "mission", "now": "2"})
    assert progress.locator("dd").all_text_contents() == ["2", "2", "0", "0", "0", "complete"]
