"""Browser contract tests for the shared run workspace.

What: checks run selection, tab sharing, refresh failures and explicit history access.
When called: pytest runs this module against a locally served web app and API.
Why: stale or mixed run state can mislead rescue operators even when the API is correct.
"""

from __future__ import annotations

import os
from playwright.sync_api import Page, expect


API_ORIGIN = os.environ.get("SPACE_RESCUE_TEST_API", "http://127.0.0.1:8000")


def test_can_create_run_and_share_it_between_tabs(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs",
        lambda route: route.fulfill(
            status=201,
            json={"application_run_id": "RUN-UI", "central_id": "CENTRAL-UI"},
        ),
    )
    page.route(
        f"{API_ORIGIN}/runs/RUN-UI/state",
        lambda route: route.fulfill(status=200, json={"missions": []}),
    )

    expect(page.get_by_role("tab", name="Operations")).to_be_visible()
    expect(page.get_by_role("tab", name="Exploration")).to_be_visible()
    page.get_by_label("Application run ID").fill("RUN-UI")
    page.get_by_label("Central ID").fill("CENTRAL-UI")
    page.get_by_role("button", name="Create run").click()
    expect(page.get_by_text("RUN-UI", exact=True)).to_be_visible()

    page.get_by_role("tab", name="Exploration").click()
    expect(page.get_by_text("RUN-UI", exact=True)).to_be_visible()


def test_open_unknown_run_shows_unavailable_state(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/MISSING/state",
        lambda route: route.fulfill(status=404, json={"detail": "unknown run"}),
    )
    page.get_by_label("Application run ID").fill("MISSING")
    page.get_by_role("button", name="Open run").click()
    expect(page.get_by_role("alert")).to_contain_text("unavailable")


def test_refresh_failure_keeps_snapshot_and_marks_it_stale(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-STALE/state",
        lambda route: route.fulfill(status=503, json={"detail": "offline"}),
    )
    page.get_by_label("Application run ID").fill("RUN-STALE")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("button", name="Refresh state").click()
    expect(page.get_by_role("status")).to_contain_text("stale")


def test_history_is_loaded_only_after_explicit_action(workspace_page: Page):
    page = workspace_page
    history_requests: list[str] = []

    def record_history(route):
        history_requests.append(route.request.url)
        route.fulfill(status=200, json=[])

    page.route(f"{API_ORIGIN}/runs/RUN-HISTORY/history", record_history)
    page.get_by_label("Application run ID").fill("RUN-HISTORY")
    page.get_by_role("button", name="Open run").click()
    assert history_requests == []
    page.get_by_role("button", name="Load call history").click()
    expect(page.get_by_text("Call history")).to_be_visible()
    assert len(history_requests) == 1


def test_operation_business_rejection_is_shown_and_not_retried(workspace_page: Page):
    page = workspace_page
    calls: list[str] = []

    def reject_operation(route):
        calls.append(route.request.url)
        route.fulfill(
            status=200,
            json={"status": "rejected", "value": None, "reason": "invalid mission"},
        )

    page.route(f"{API_ORIGIN}/runs/RUN-REJECT/operations/**", reject_operation)
    page.get_by_label("Application run ID").fill("RUN-REJECT")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Operations").click()
    page.get_by_label("Mission ID").fill("M-1")
    page.get_by_role("button", name="Register mission").click()
    expect(page.get_by_role("alert")).to_contain_text("invalid mission")
    assert len(calls) == 1


def test_keyboard_can_switch_tabs_and_reach_run_controls(workspace_page: Page):
    page = workspace_page
    page.keyboard.press("Tab")
    expect(page.locator(":focus")).to_be_visible()
    page.get_by_role("tab", name="Exploration").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("tab", name="Exploration")).to_have_attribute(
        "aria-selected", "true"
    )


def test_api_url_builder_encodes_run_identifier(workspace_page: Page):
    page = workspace_page
    page.get_by_label("Application run ID").fill("RUN/ONE")
    page.get_by_role("button", name="Open run").click()
    expect(page.get_by_text("RUN/ONE", exact=True)).to_be_visible()
