"""Browser journey for the core ten-person rescue.

What: checks a mission, fleet, request, ship response and subsequent mobilisation.
When called: pytest runs this module against the local web app and rescue API.
Why: the browser must support the complete reservation-confirmation problem.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.e2e.web.foundation.test_workspace import API_ORIGIN


def test_operator_can_register_mission_and_ships(workspace_page: Page):
    page = workspace_page
    page.route(f"{API_ORIGIN}/runs/RUN-RESCUE/state", lambda r: r.fulfill(json={"missions": []}))
    page.route(
        f"{API_ORIGIN}/runs/RUN-RESCUE/operations/**",
        lambda r: r.fulfill(
            status=200,
            json={"status": "accepted", "value": {"mission_id": "AURORA", "people_count": 10}},
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-RESCUE")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_label("Mission ID").fill("AURORA")
    page.get_by_label("Station name").fill("Aurora")
    page.get_by_label("People count").fill("10")
    page.get_by_role("button", name="Register mission").click()
    expect(page.get_by_text("AURORA", exact=True)).to_be_visible()


def test_progress_separates_confirmed_pending_and_unmet_demand(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-PROGRESS/operations/get_progress",
        lambda r: r.fulfill(
            status=200,
            json={
                "status": "accepted",
                "value": {
                    "mission_id": "AURORA",
                    "people_count": 10,
                    "confirmed_seats": 3,
                    "pending_seats": 4,
                    "unmet_seats": 3,
                },
            },
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-PROGRESS")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_label("Mission ID").fill("AURORA")
    page.get_by_role("button", name="Get progress").click()
    expect(page.get_by_text("Confirmed seats")).to_be_visible()
    expect(page.get_by_text("Pending seats")).to_be_visible()
    expect(page.get_by_text("Unmet demand")).to_be_visible()


def test_partial_response_is_final_and_further_help_can_be_requested(workspace_page: Page):
    page = workspace_page
    outcomes = iter([
        {"status": "accepted", "value": {"request_id": "REQ-1", "confirmed_seats": 3}, "reason": None},
        {"status": "accepted", "value": {"request_id": "REQ-2"}, "reason": None},
    ])
    page.route(
        f"{API_ORIGIN}/runs/RUN-PARTIAL/operations/**",
        lambda r: r.fulfill(status=200, json=next(outcomes)),
    )
    page.get_by_label("Application run ID").fill("RUN-PARTIAL")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_role("button", name="Requests").click()
    page.get_by_label("Request ID").fill("REQ-1")
    page.get_by_label("Confirmed seats").fill("3")
    page.get_by_role("button", name="Record response").click()
    expect(page.get_by_text("final", exact=False)).to_be_visible()
    page.get_by_role("button", name="Create request").click()
    expect(page.get_by_text("REQ-2", exact=True)).to_be_visible()
