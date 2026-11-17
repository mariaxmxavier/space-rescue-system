"""Complete the reservation-confirmation rescue through real browser operations.

When: browser acceptance runs against the isolated live API.
Why: submitted UI payloads must preserve accounting and final outcomes end to end.
"""

from playwright.sync_api import Page, expect

from tests.e2e.web.support import choose, submit


def test_ten_person_rescue_with_partial_refusal_and_further_mobilisation(live_workspace_page: Page):
    """Register fleet, allocate requests, receive mixed answers and finish at ten confirmed."""
    page = live_workspace_page
    page.get_by_role("button", name="Experiments", exact=True).click()
    page.get_by_role("button", name="Add mobilisation policy", exact=True).click()
    policy = page.get_by_role("group", name="Mobilisation policy", exact=True)
    policy.get_by_label("Policy ID", exact=True).fill("early")
    policy.get_by_label("Name", exact=True).fill("Earliest")
    page.get_by_label("Application run ID", exact=True).fill("browser-rescue")
    page.get_by_label("Central ID", exact=True).fill("central")
    page.get_by_role("button", name="Create run", exact=True).click()
    expect(page.locator("#refresh-status")).to_contain_text("Updated")
    choose(page, "Missions")
    submit(
        page,
        "register_mission",
        {"mission_id": "mission", "station_name": "Aurora", "people_count": 10, "created_at": "0"},
    )
    choose(page, "Fleet")
    for ship, seats, arrival in [("A", 6, 1), ("B", 4, 2)]:
        submit(page, "register_ship", {"ship_id": ship, "name": ship})
        submit(
            page,
            "publish_availability",
            {
                "availability.availability_id": f"av-{ship}",
                "availability.ship_id": ship,
                "availability.total_seats": seats,
                "availability.arrival_estimate_seconds": str(arrival),
                "availability.available": True,
                "availability.recorded_at": "0",
            },
        )
        submit(
            page,
            "publish_offer",
            {
                "offer_id": f"offer-{ship}",
                "mission_id": "mission",
                "ship_id": ship,
                "revision.revision_id": f"rev-{ship}",
                "revision.revision_number": 1,
                "revision.capacity": seats,
                "revision.arrival_estimate_seconds": str(arrival),
                "revision.available": True,
                "revision.recorded_at": "0",
            },
        )
    choose(page, "Mobilisation")
    mobilisation = submit(
        page,
        "mobilise",
        {"mission_id": "mission", "policy_id": "early", "policy_revision": 1, "now": "0"},
    )
    expect(mobilisation.locator(".result-summary")).to_contain_text("applied")
    choose(page, "Requests")
    for ship, seats in [("A", 6), ("B", 4)]:
        submit(
            page,
            "create_request",
            {
                "command_id": f"request-{ship}",
                "mission_id": "mission",
                "ship_id": ship,
                "requested_seats": seats,
                "revision_id": f"rev-{ship}",
                "now": "0",
                "response_deadline": "10",
            },
        )
    state = page.evaluate(
        """async () => { const {createApiClient}=await import('/shared/api/client.js'); return createApiClient().readState('browser-rescue'); }"""
    )
    requests = {r["ship_id"]: r["request_id"] for r in state["missions"][0]["requests"]}
    choose(page, "Communication")
    for ship, outcome, confirmed in [("A", "partially_accepted", 4), ("B", "refused", 0)]:
        submit(
            page,
            "record_response",
            {
                "message_id": f"msg-{ship}",
                "delivery_id": f"delivery-{ship}",
                "attempt_number": 1,
                "request_id": requests[ship],
                "outcome": outcome,
                "confirmed_seats": confirmed,
                "sent_at": "1",
                "received_at": "1",
            },
        )
    choose(page, "Missions")
    progress = submit(page, "get_progress", {"mission_id": "mission", "now": "1"})
    expect(progress).to_contain_text("Confirmed seats")
    expect(progress).to_contain_text("Unmet demand")
    choose(page, "Mobilisation")
    submit(
        page,
        "mobilise",
        {"mission_id": "mission", "policy_id": "early", "policy_revision": 1, "now": "2"},
    )
    choose(page, "Requests")
    for ship, seats in [("A", 2), ("B", 4)]:
        submit(
            page,
            "create_request",
            {
                "command_id": f"replacement-{ship}",
                "mission_id": "mission",
                "ship_id": ship,
                "requested_seats": seats,
                "revision_id": f"rev-{ship}",
                "now": "2",
                "response_deadline": "10",
            },
        )
    state = page.evaluate(
        """async () => { const {createApiClient}=await import('/shared/api/client.js'); return createApiClient().readState('browser-rescue'); }"""
    )
    pending = [r for r in state["missions"][0]["requests"] if r["outcome"] == "pending"]
    choose(page, "Communication")
    for r in pending:
        submit(
            page,
            "record_response",
            {
                "message_id": f"final-{r['ship_id']}",
                "delivery_id": f"final-delivery-{r['ship_id']}",
                "attempt_number": 1,
                "request_id": r["request_id"],
                "outcome": "accepted",
                "confirmed_seats": r["requested_seats"],
                "sent_at": "3",
                "received_at": "3",
            },
        )
    choose(page, "Missions")
    form = submit(page, "get_progress", {"mission_id": "mission", "now": "3"})
    expect(form).to_contain_text("complete")
    assert form.locator("dd").all_text_contents() == ["10", "10", "0", "0", "0", "complete"]


def test_cancelled_and_expired_requests_remain_final(live_workspace_page: Page):
    """Close requests using both browser actions and show that later answers add no seats."""
    from tests.e2e.web.support import prepare_run

    page = live_workspace_page
    prepare_run(page, "finality")
    choose(page, "Requests")
    submit(
        page,
        "create_request",
        {
            "command_id": "cancel",
            "mission_id": "mission",
            "ship_id": "A",
            "requested_seats": 2,
            "revision_id": "revision",
            "now": "0",
            "response_deadline": "2",
        },
    )
    state = page.evaluate(
        """async () => {const {createApiClient}=await import('/shared/api/client.js');return createApiClient().readState('finality')}"""
    )
    request = state["missions"][0]["requests"][0]["request_id"]
    cancelled = submit(
        page,
        "cancel_request",
        {"mission_id": "mission", "request_id": request, "now": "1", "reason": "not needed"},
    )
    expect(cancelled.locator(".result-summary")).to_contain_text("applied")
    choose(page, "Communication")
    late = submit(
        page,
        "record_response",
        {
            "message_id": "after-cancel",
            "delivery_id": "delivery-cancel",
            "attempt_number": 1,
            "request_id": request,
            "outcome": "accepted",
            "confirmed_seats": 2,
            "sent_at": "1",
            "received_at": "1",
        },
    )
    expect(late.locator(".result-summary")).to_contain_text("ignored")
    choose(page, "Requests")
    submit(
        page,
        "create_request",
        {
            "command_id": "expire",
            "mission_id": "mission",
            "ship_id": "A",
            "requested_seats": 2,
            "revision_id": "revision",
            "now": "1",
            "response_deadline": "2",
        },
    )
    state = page.evaluate(
        """async () => {const {createApiClient}=await import('/shared/api/client.js');return createApiClient().readState('finality')}"""
    )
    request = state["missions"][0]["requests"][-1]["request_id"]
    expired = submit(
        page, "expire_request", {"mission_id": "mission", "request_id": request, "now": "2"}
    )
    expect(expired.locator(".result-summary")).to_contain_text("applied")
    choose(page, "Communication")
    late = submit(
        page,
        "record_response",
        {
            "message_id": "after-expire",
            "delivery_id": "delivery-expire",
            "attempt_number": 1,
            "request_id": request,
            "outcome": "accepted",
            "confirmed_seats": 2,
            "sent_at": "1",
            "received_at": "3",
        },
    )
    expect(late.locator(".result-summary")).to_contain_text("ignored")
    choose(page, "Missions")
    progress = submit(page, "get_progress", {"mission_id": "mission", "now": "3"})
    assert progress.locator("dd").all_text_contents() == [
        "2",
        "0",
        "0",
        "2",
        "2",
        "needs_more_help",
    ]
