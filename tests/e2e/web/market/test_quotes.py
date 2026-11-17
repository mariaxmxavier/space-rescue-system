"""Real browser quote lifecycle and shared-capacity acceptance checks.

When: independent market journeys run against the local API.
Why: held seats, pending commitments and confirmed seats must remain distinct.
"""

from playwright.sync_api import Page, expect

from tests.e2e.web.support import choose, prepare_run, submit


def test_quote_hold_acceptance_and_cross_mission_capacity(live_workspace_page: Page):
    """Hold a quote, inspect its held seats, accept it and reject overcommit."""
    page = live_workspace_page
    invoke = prepare_run(page, "quote-accept")
    choose(page, "Quotes")
    submit(page, "request_quotes", {"mission_id": "mission", "now": "0", "response_deadline": "10"})
    state = page.evaluate(
        """async () => {const {createApiClient}=await import('/shared/api/client.js');return createApiClient().readState('quote-accept')}"""
    )
    rfq = state["market"]["rfqs"][0]["rfq_id"]
    submit(
        page,
        "record_quote",
        {
            "offer_id": "quote",
            "rfq_id": rfq,
            "offered_seats": 2,
            "arrival_estimate_seconds": "1",
            "expires_at": "10",
            "recorded_at": "0",
            "now": "0",
        },
    )
    expect(page.get_by_text("quote: 2 seats held until 10", exact=True)).to_be_visible()
    accepted = submit(
        page,
        "accept_quote",
        {"command_id": "accept", "mission_id": "mission", "quote_id": "quote", "now": "1"},
    )
    expect(accepted.locator(".result-summary")).to_contain_text("applied")
    expect(page.get_by_text("No held quotes", exact=True)).to_be_visible()
    invoke(
        "register_mission",
        {"mission_id": "other", "station_name": "Other", "people_count": 2, "created_at": "0"},
    )
    invoke(
        "publish_offer",
        {
            "offer_id": "other-offer",
            "mission_id": "other",
            "ship_id": "A",
            "revision": {
                "revision_id": "other-revision",
                "revision_number": 1,
                "capacity": 2,
                "arrival_estimate_seconds": "1",
                "available": True,
                "recorded_at": "0",
            },
        },
    )
    choose(page, "Requests")
    rejected = submit(
        page,
        "create_request",
        {
            "command_id": "overcommit",
            "mission_id": "other",
            "ship_id": "A",
            "requested_seats": 1,
            "revision_id": "other-revision",
            "now": "2",
        },
    )
    expect(rejected.locator(".result-summary")).to_contain_text("rejected")
    expect(rejected).to_contain_text("insufficient_capacity")
    choose(page, "Fleet")
    expect(page.get_by_role("heading", name="Pending commitments", exact=True)).to_be_visible()
    expect(page.get_by_text("mission: request", exact=False)).to_be_visible()


def test_quote_rejection_and_expiry_release_held_capacity(live_workspace_page: Page):
    """Close two independent held quotes through their browser controls."""
    page = live_workspace_page
    invoke = prepare_run(page, "quote-release")
    invoke("request_quotes", {"mission_id": "mission", "now": "0"})
    state = page.evaluate(
        """async () => {const {createApiClient}=await import('/shared/api/client.js');return createApiClient().readState('quote-release')}"""
    )
    rfq = state["market"]["rfqs"][0]["rfq_id"]
    choose(page, "Quotes")
    submit(
        page,
        "record_quote",
        {
            "offer_id": "reject",
            "rfq_id": rfq,
            "offered_seats": 1,
            "arrival_estimate_seconds": "1",
            "expires_at": "5",
            "recorded_at": "0",
            "now": "0",
        },
    )
    submit(page, "reject_quote", {"quote_id": "reject", "now": "1"})
    submit(
        page,
        "record_quote",
        {
            "offer_id": "expire",
            "rfq_id": rfq,
            "offered_seats": 1,
            "arrival_estimate_seconds": "1",
            "expires_at": "5",
            "recorded_at": "1",
            "now": "1",
        },
    )
    submit(page, "expire_quotes", {"now": "5"})
    expect(page.get_by_text("No held quotes", exact=True)).to_be_visible()
