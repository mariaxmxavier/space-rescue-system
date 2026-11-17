"""Inspect real mission records, decisions and explicit call history in the browser.

When: independent prepared runs contain request and allocation outcomes.
Why: complete explanations remain inspectable separately from mission accounting.
"""

from playwright.sync_api import Page, expect

from tests.e2e.web.support import choose, prepare_run, submit


def test_decision_progress_and_histories_match_committed_records(live_workspace_page: Page):
    """Read an allocation trace, mission history, and complete HTTP activity."""
    page = live_workspace_page
    invoke = prepare_run(page, "inspection")
    decision = invoke(
        "mobilise",
        {"mission_id": "mission", "policy_id": "early", "policy_revision": 1, "now": "0"},
    )
    decision_id = decision["value"]["decision_id"]
    invoke(
        "create_request",
        {
            "command_id": "request",
            "mission_id": "mission",
            "ship_id": "A",
            "requested_seats": 2,
            "revision_id": "revision",
            "now": "0",
        },
    )
    choose(page, "Decisions")
    result = submit(page, "get_decision", {"decision_id": decision_id})
    result.get_by_text("Complete result", exact=True).click()
    expect(result.locator("pre")).to_contain_text('"evaluations"')
    expect(result.locator("pre")).to_contain_text('"proposed_seats"')
    choose(page, "Mission history")
    progress = submit(page, "get_progress", {"mission_id": "mission", "now": "1"})
    expect(progress).to_contain_text("Confirmed seats")
    expect(progress).to_contain_text("Pending seats")
    history = submit(page, "get_history", {"mission_id": "mission"})
    history.get_by_text("Complete result", exact=True).click()
    expect(history.locator("pre")).to_contain_text("request")
    page.get_by_role("button", name="Load call history", exact=True).click()
    expect(page.locator("#history-content pre")).to_contain_text('"input"')
    expect(page.locator("#history-content pre")).to_contain_text('"response"')
    expect(page.locator("#history-content pre")).to_contain_text("get_history")


def test_all_22_operations_remain_discoverable(workspace_page: Page):
    """Audit mounted browser actions against the API's public operation registry."""
    from rescue.api.operations import OPERATIONS

    page = workspace_page
    for capability in [
        "Missions",
        "Fleet",
        "Quotes",
        "Requests",
        "Mobilisation",
        "Communication",
        "Experiments",
        "Run inspection",
        "Mission history",
        "Decisions",
    ]:
        choose(page, capability)
    actual = page.locator("form[data-operation]").evaluate_all(
        "forms => forms.map(form => form.dataset.operation)"
    )
    assert set(actual) == set(OPERATIONS)
