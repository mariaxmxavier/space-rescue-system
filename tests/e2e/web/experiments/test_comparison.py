"""Browser journeys for configured scenario comparisons.

What: checks run-time experiment configuration and truthful comparison labels.
When called: pytest runs this module against the local web app and rescue API.
Why: simulated baselines must remain distinguishable from the live rescue run.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.e2e.web.foundation.test_workspace import API_ORIGIN


def test_run_setup_accepts_scenario_and_multiple_policies(workspace_page: Page):
    page = workspace_page
    submitted: list[dict] = []

    def create_run(route):
        submitted.append(route.request.post_data_json)
        route.fulfill(status=201, json={"application_run_id": "RUN-EXP", "central_id": "CENTRAL"})

    page.route(f"{API_ORIGIN}/runs", create_run)
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_label("Application run ID").fill("RUN-EXP")
    page.get_by_label("Central ID").fill("CENTRAL")
    page.get_by_role("button", name="Add mobilisation policy").click()
    page.get_by_role("button", name="Add scenario").click()
    expect(page.get_by_label("Scenario ID")).to_be_visible()
    expect(page.get_by_label("Policy ID")).to_have_count(1)


def test_comparison_is_labelled_as_simulation_of_configured_baseline(workspace_page: Page):
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/RUN-EXP/operations/compare",
        lambda r: r.fulfill(
            status=200,
            json={"status": "accepted", "value": {"scenario_id": "SCENARIO-1", "results": []}},
        ),
    )
    page.get_by_label("Application run ID").fill("RUN-EXP")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Experiments").click()
    page.get_by_label("Scenario ID").fill("SCENARIO-1")
    page.get_by_role("button", name="Compare policies").click()
    expect(page.get_by_text("Simulation baseline", exact=False)).to_be_visible()
    expect(page.get_by_text("Live mission", exact=False)).to_be_visible()


def test_missing_scenario_does_not_fabricate_comparison_results(workspace_page: Page):
    page = workspace_page
    page.get_by_label("Application run ID").fill("RUN-EMPTY")
    page.get_by_role("button", name="Open run").click()
    page.get_by_role("tab", name="Exploration").click()
    page.get_by_role("button", name="Experiments").click()
    page.get_by_role("button", name="Compare policies").click()
    expect(page.get_by_role("alert")).to_contain_text("scenario")
    expect(page.get_by_text("Simulation baseline")).to_have_count(0)
