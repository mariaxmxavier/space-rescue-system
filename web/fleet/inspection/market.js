/** Render availability revisions and seat commitments from an API snapshot.
 *
 * What: exposes the market's own availability, holds and request records.
 * When called: Fleet mounts or the selected run snapshot changes.
 * Why: distinguishing capacity states prevents a hold from appearing as confirmed transport.
 */
export function renderFleetInspection(snapshot) {
  const section = document.createElement("section");
  section.setAttribute("aria-label", "Fleet capacity details");
  appendRecordList(section, "Availability history", snapshot?.market?.availabilities ?? [], (item) =>
    `${item.ship_id}: ${item.total_seats} seats offered; arrival ${item.arrival_estimate_seconds}; ${item.available ? "available" : "unavailable"} at ${item.recorded_at}`
  );
  appendRecordList(section, "Held seats", (snapshot?.market?.quotes ?? []).filter((quote) => quote.status === "held"), (quote) =>
    `${quote.offer_id}: ${quote.offered_seats} seats held until ${quote.expires_at}`
  );
  const requests = (snapshot?.missions ?? []).flatMap((mission) =>
    (mission.requests ?? []).map((request) => ({ missionId: mission.mission_id, request }))
  );
  appendRecordList(section, "Confirmed seats", requests.filter(({ request }) => request.outcome === "accepted" || request.outcome === "partially_accepted"), ({ missionId, request }) =>
    `${missionId}: request ${request.request_id}; confirmed ${request.confirmed_seats ?? request.requested_seats}`
  );
  appendRecordList(section, "Pending commitments", requests.filter(({ request }) => request.outcome === "pending" || request.status === "pending"), ({ missionId, request }) =>
    `${missionId}: request ${request.request_id}; ${request.requested_seats} seats awaiting response`
  );
  const details = document.createElement("details");
  const summary = document.createElement("summary"); summary.textContent = "Complete fleet, offer revisions and shared capacity records";
  const pre = document.createElement("pre"); pre.textContent = JSON.stringify({market:snapshot?.market ?? null,requests},null,2);
  details.append(summary,pre); section.append(details);
  return section;
}

function appendRecordList(parent, title, records, describe) {
  const group = document.createElement("section");
  const heading = document.createElement("h3");
  heading.textContent = title;
  group.append(heading);
  const list = document.createElement("ul");
  if (records.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No records";
    list.append(empty);
  }
  for (const record of records) {
    const item = document.createElement("li");
    item.textContent = describe(record);
    list.append(item);
  }
  group.append(list);
  parent.append(group);
}
