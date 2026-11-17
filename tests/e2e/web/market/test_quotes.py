"""Browser checks for quote lifecycle and shared fleet capacity.

What: verifies operator-visible quote decisions and cross-mission capacity results.
When called: pytest runs this module against the local web app and rescue API.
Why: quote holds and accepted reservations have different accounting effects.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.e2e.web.foundation.test_workspace import API_ORIGIN


def test_quote_lifecycle_exposes_hold_and_final_outcome(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-QUOTE/operations/accept_quote",
        lambda r: r.fulfill(
            status=200,
            json={"status": "accepted", "value": {"request_id": "REQ-1"}, "reason": None},
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-QUOTE")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_role("button", name="Quotes").click()
    expect(page.get_by_text("Held capacity", exact=False)).to_be_visible()
    page.get_by_label("Quote ID").fill("QUOTE-1")
    page.get_by_role("button", name="Accept quote").click()
    expect(page.get_by_text("REQ-1", exact=True)).to_be_visible()


def test_cross_mission_overcommit_displays_server_reason(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-CAPACITY/operations/accept_quote",
        lambda r: r.fulfill(
            status=200,
            json={"status": "rejected", "value": None, "reason": "capacity is already committed"},
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-CAPACITY")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_role("button", name="Quotes").click()
    page.get_by_label("Quote ID").fill("QUOTE-OVERBOOK")
    page.get_by_role("button", name="Accept quote").click()
    expect(page.get_by_role("alert")).to_contain_text("capacity is already committed")


def test_availability_revisions_distinguish_offered_and_confirmed_seats(workspace_page: Page):
    page = workspace_page
    page.get_by_label("Application run ID").fill("RUN-FLEET")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Fleet").click()
    expect(page.get_by_text("Availability history")).to_be_visible()
    expect(page.get_by_text("Confirmed seats")).to_be_visible()
    expect(page.get_by_text("Held seats")).to_be_visible()
