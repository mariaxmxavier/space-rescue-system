# Browser View Data Model

These are presentation records over API data; they do not own business rules.

| View | Fields and relationships | Behaviour |
| --- | --- | --- |
| Workspace | selected run ID, tab, latest snapshot, refresh time, loading/error | Run switch invalidates earlier in-flight responses; unavailable runs are visible. |
| Mission | station, demand, progress, requests, decisions, history | Distinguish confirmed, pending, held and unmet quantities; API determines status. |
| Fleet and market | ships, availability versions, offers, RFQs, quotes, holds | Preserve version and commitment distinctions; API controls capacity. |
| Request | mission, ship, quantity, response, outcome | API decides finality and accepted quantity. |
| Communication | message, delivery, session, sequence control, reports | Present classification and recovery without applying effects twice. |
| Experiments | policies, scenarios, baseline, comparison results and timeline | Clearly label simulation and baseline apart from live mission data. |
| Activity | ordered call input and complete outcome | Fetch history explicitly; prior history responses are nested. |
| Action form | typed fields, validation, pending status, full result | Derive schema from actual commands and codec; retain inputs on error; no automatic retries. |
