"""Configure complete experiment baselines and compare policies through the browser.

When: a user prepares an isolated run with nested scenario and policy controls.
Why: experimental timelines must be genuine results with a labelled baseline.
"""

from playwright.sync_api import Page, expect

from tests.e2e.web.support import choose


def fill(group, values):
    """Fill exact labels within a repeatable editor's accessible group."""
    for label, value in values.items():
        control = group.get_by_label(label, exact=True)
        if isinstance(value, bool):
            control.set_checked(value)
        else:
            control.fill(str(value))


def test_configured_scenario_and_two_policies_produce_real_comparison(live_workspace_page: Page):
    """Create baseline entities and response rules, then inspect both retained timelines."""
    page = live_workspace_page
    choose(page, "Experiments")
    for policy_id, strategy in [("early", "earliest_arrival"), ("large", "largest_capacity")]:
        page.get_by_role("button", name="Add mobilisation policy", exact=True).click()
        policy = page.get_by_role("group", name="Mobilisation policy", exact=True).last
        fill(policy, {"Policy ID": policy_id, "Revision": 1, "Name": policy_id})
        policy.get_by_label("Selection criteria", exact=True).select_option(strategy)
    page.get_by_role("button", name="Add scenario", exact=True).click()
    scenario = page.get_by_role("group", name="Scenario", exact=True)
    fill(
        scenario,
        {
            "Scenario ID": "rescue",
            "Revision": 1,
            "Name": "Rescue",
            "Time horizon seconds": "10",
            "Seed": 1,
            "Event budget": 100,
            "Market ID": "market",
        },
    )
    scenario.get_by_role("button", name="Add mission", exact=True).click()
    mission = scenario.get_by_role("group", name="Mission 1", exact=True)
    fill(
        mission,
        {"Mission ID": "mission", "Station name": "Aurora", "People count": 2, "Created at": "0"},
    )
    scenario.get_by_role("button", name="Add ship", exact=True).click()
    fill(
        scenario.get_by_role("group", name="Ship 1", exact=True), {"Ship ID": "A", "Name": "Atlas"}
    )
    scenario.get_by_role("button", name="Add availability", exact=True).click()
    fill(
        scenario.get_by_role("group", name="Availability 1", exact=True),
        {
            "Availability ID": "availability",
            "Ship ID": "A",
            "Total seats": 2,
            "Arrival estimate seconds": "1",
            "Available": True,
            "Recorded at": "0",
        },
    )
    scenario.get_by_role("button", name="Add offer", exact=True).click()
    offer = scenario.get_by_role("group", name="Offer 1", exact=True)
    fill(offer, {"Offer ID": "offer", "Mission ID": "mission", "Ship ID": "A"})
    offer.get_by_role("button", name="Add revision", exact=True).click()
    fill(
        offer.get_by_role("group", name="Revision 1", exact=True),
        {
            "Revision ID": "revision",
            "Revision number": 1,
            "Capacity": 2,
            "Arrival estimate seconds": "1",
            "Available": True,
            "Recorded at": "0",
        },
    )
    scenario.get_by_role("button", name="Add response rule", exact=True).click()
    rule = scenario.get_by_role("group", name="Response rule 1", exact=True)
    fill(rule, {"Ship ID": "A", "Request ordinal": 1})
    rule.get_by_label("Outcome", exact=True).select_option("accepted")
    page.get_by_label("Application run ID", exact=True).fill("experiments")
    page.get_by_label("Central ID", exact=True).fill("central")
    page.get_by_role("button", name="Create run", exact=True).click()
    expect(page.locator("#refresh-status")).to_contain_text("Updated")
    form = page.locator('form[data-operation="compare"]')
    fill(
        form,
        {
            "Scenario ID": "rescue",
            "Scenario revision": 1,
            "Policy ID": "early",
            "Policy revision": 1,
        },
    )
    form.get_by_role("button", name="Add comparison policy", exact=True).click()
    second = form.get_by_role("group", name="Comparison policy 2", exact=True)
    fill(second, {"Policy ID": "large", "Policy revision": 1})
    form.get_by_role("button", name="Compare policies", exact=True).click()
    result = form.locator("+ section")
    expect(result.locator(".result-summary")).to_contain_text("applied")
    result.get_by_text("Complete result", exact=True).click()
    expect(
        result.get_by_role("heading", name="Recorded mission timeline", exact=True)
    ).to_have_count(2)
    expect(result.locator("pre")).to_contain_text('"early"')
    expect(result.locator("pre")).to_contain_text('"large"')
    expect(page.get_by_text("Simulation baseline:", exact=False)).to_be_visible()
    expect(page.get_by_text("Live mission:", exact=False)).to_be_visible()


def test_missing_configuration_shows_actionable_explanation(workspace_page: Page):
    """Empty comparison inputs produce useful feedback without invented runs."""
    page = workspace_page
    choose(page, "Experiments")
    form = page.locator('form[data-operation="compare"]')
    form.get_by_role("button", name="Compare policies", exact=True).click()
    expect(form.locator("+ section").get_by_role("alert")).to_contain_text("scenario")
    expect(form.locator("+ section pre")).to_have_count(0)
