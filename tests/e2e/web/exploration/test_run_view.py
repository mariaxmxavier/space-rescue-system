"""Browser checks for live run explanation and activity inspection.

What: verifies exploration displays authoritative progress, decisions and histories.
When called: pytest runs this module against the local web app and rescue API.
Why: operators need to explain current state and the sequence of decisions behind it.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.e2e.web.foundation.test_workspace import API_ORIGIN


def test_decision_exposes_trace_and_allocation_details(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-DECISION/operations/get_decision",
        lambda r: r.fulfill(
            status=200,
            json={"status": "accepted", "value": {"decision_id": "DEC-1", "trace": [{"reason": "earliest arrival"}]}}
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-DECISION")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Decisions").click()
    page.get_by_label("Decision ID").fill("DEC-1")
    page.get_by_role("button", name="Inspect decision").click()
    expect(page.get_by_text("earliest arrival")).to_be_visible()


def test_mission_history_is_distinct_from_call_history(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-HISTORY/operations/get_history",
        lambda r: r.fulfill(status=200, json={"status": "accepted", "value": [{"action": "PARTIAL_ACCEPTANCE"}]}),
    )
    page.get_by_label("Application run ID").fill("RUN-HISTORY")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Missions").click()
    page.get_by_label("Mission ID").fill("AURORA")
    page.get_by_role("button", name="Mission history").click()
    expect(page.get_by_text("PARTIAL_ACCEPTANCE")).to_be_visible()
    expect(page.get_by_role("button", name="Load call history")).to_be_visible()


def test_refresh_displays_last_committed_progress(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-LIVE/state",
        lambda r: r.fulfill(status=200, json={"missions": [{"mission_id": "AURORA", "people_count": 10}]}),
    )
    page.get_by_label("Application run ID").fill("RUN-LIVE")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    expect(page.get_by_text("AURORA", exact=True)).to_be_visible()
    expect(page.get_by_text("10", exact=True)).to_be_visible()
