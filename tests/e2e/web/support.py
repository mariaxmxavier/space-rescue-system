"""Browser helpers that use visible forms and inspect authoritative API state.

When: browser journeys repeat navigation and operation submission.
Why: selectors target the same operation a person chooses without duplicating policy.
"""

from playwright.sync_api import Page, expect


def choose(page: Page, capability: str):
    """Choose one discoverable capability and return its visible operation controls."""
    page.get_by_role("button", name=capability, exact=True).click()
    return page


def operation(page: Page, name: str):
    """Find the one visible form for an exact public operation."""
    return page.locator(f'form[data-operation="{name}"]:visible')


def submit(page: Page, name: str, values: dict):
    """Fill explicit labelled inputs and submit once, waiting for a complete result."""
    form = operation(page, name)
    for key, value in values.items():
        control = form.locator(f'[name="{key}"]')
        if isinstance(value, bool):
            control.set_checked(value)
        elif control.evaluate("element => element.tagName") == "SELECT":
            control.select_option(str(value))
        else:
            control.fill(str(value))
    form.locator('button[type="submit"]').click()
    expect(form.locator(".result-summary")).to_be_visible()
    return form


def open_run(page: Page, run_id: str):
    """Reopen a known run through the shell's visible input and button."""
    page.get_by_label("Application run ID", exact=True).fill(run_id)
    page.get_by_role("button", name="Open run", exact=True).click()
    expect(page.locator("#selected-run")).to_have_text(run_id)


def prepare_run(page: Page, run_id: str, demand=2, capacity=2):
    """Prepare real API records for an independent browser inspection journey."""
    from urllib.parse import parse_qs, urlparse

    origin = parse_qs(urlparse(page.url).query)["api"][0]
    response = page.request.post(
        f"{origin}/runs",
        data={
            "application_run_id": run_id,
            "central_id": "central",
            "policies": [
                {
                    "policy_id": "early",
                    "revision": 1,
                    "name": "Earliest",
                    "selection_criteria": "earliest_arrival",
                }
            ],
        },
    )
    assert response.status == 201, response.text()

    def invoke(name, values, scalar=False):
        response = page.request.post(
            f"{origin}/runs/{run_id}/operations/{name}",
            data=values if scalar else {"command": values},
        )
        assert response.ok, response.text()
        return response.json()

    invoke(
        "register_mission",
        {
            "mission_id": "mission",
            "station_name": "Aurora",
            "people_count": demand,
            "created_at": "0",
        },
    )
    invoke("register_ship", {"ship_id": "A", "name": "Atlas"})
    invoke(
        "publish_availability",
        {
            "availability": {
                "availability_id": "availability",
                "ship_id": "A",
                "total_seats": capacity,
                "arrival_estimate_seconds": "1",
                "available": True,
                "recorded_at": "0",
            }
        },
    )
    invoke(
        "publish_offer",
        {
            "offer_id": "offer",
            "mission_id": "mission",
            "ship_id": "A",
            "revision": {
                "revision_id": "revision",
                "revision_number": 1,
                "capacity": capacity,
                "arrival_estimate_seconds": "1",
                "available": True,
                "recorded_at": "0",
            },
        },
    )
    open_run(page, run_id)
    expect(page.locator("#refresh-status")).to_contain_text("Updated")
    return invoke
