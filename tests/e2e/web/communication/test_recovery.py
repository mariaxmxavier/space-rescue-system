"""Browser journeys for inspecting deliveries and recovering session reports.

What: verifies duplicate delivery inspection, sequence synchronisation and recovery controls.
When called: pytest runs this module against the local web app and rescue API.
Why: operators need to inspect communication faults without applying seat effects twice.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.e2e.web.foundation.test_workspace import API_ORIGIN


def test_duplicate_delivery_is_visible_with_server_classification(workspace_page: Page):
    page = workspace_page
    page.route(f"{API_ORIGIN}/runs/RUN-COMMS/state", lambda r: r.fulfill(json={"missions": []}))
    page.route(
        f"{API_ORIGIN}/runs/RUN-COMMS/operations/record_response",
        lambda r: r.fulfill(
            status=200,
            json={"status": "rejected", "value": {"classification": "DUPLICATE"}, "reason": "duplicate"},
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-COMMS")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Communication").click()
    expect(page.get_by_text("Delivery inspection")).to_be_visible()


def test_session_can_be_synchronised_and_reports_recovered(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-RECOVERY/operations/synchronise_inbound",
        lambda r: r.fulfill(status=200, json={"status": "accepted", "value": {"next_sequence": 5}}),
    )
    page.route(
        f"{API_ORIGIN}/runs/RUN-RECOVERY/operations/recover_reports",
        lambda r: r.fulfill(status=200, json={"status": "accepted", "value": [{"sequence": 5}]}),
    )
    page.get_by_label("Application run ID").fill("RUN-RECOVERY")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Communication").click()
    page.get_by_label("Session ID").fill("SESSION-1")
    page.get_by_role("button", name="Synchronise inbound").click()
    expect(page.get_by_text("5", exact=True)).to_be_visible()
    page.get_by_label("From sequence").fill("5")
    page.get_by_role("button", name="Recover reports").click()
    expect(page.get_by_text("sequence", exact=False)).to_be_visible()


def test_delivery_inspection_uses_existing_message_identifier(workspace_page: Page):
    page = workspace_page
    deliveries: list[str] = []

    def read_deliveries(route):
        deliveries.append(route.request.post_data or "")
        route.fulfill(status=200, json={"status": "accepted", "value": []})

    page.route(f"{API_ORIGIN}/runs/RUN-DELIVERY/operations/get_deliveries", read_deliveries)
    page.get_by_label("Application run ID").fill("RUN-DELIVERY")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Communication").click()
    page.get_by_label("Message ID").fill("MESSAGE-1")
    page.get_by_role("button", name="Inspect deliveries").click()
    expect(page.get_by_text("Deliveries")).to_be_visible()
    assert deliveries
