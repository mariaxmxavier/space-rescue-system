/**
 * What: renders every system view from one committed simulation snapshot.
 * When called: the shared playback cursor changes.
 * Why: historical mission, fleet and audit views must always describe the same instant.
 */
export function renderSnapshot({ root, state, progress, missionProgress, missionId, onMissionSelect }) {
  const doc = root.ownerDocument;
  const view = (name) => root.querySelector(`[data-view="${name}"]`);
  const missions = array(state.missions);
  const mission = missions.find((item) => item.mission_id === missionId) || missions[0];
  const selectedProgress = missionProgress?.[mission?.mission_id] || (missions[0] === mission ? progress : null);
  const market = state.market || {};
  const requests = missions.flatMap((item) => array(item.requests));
  const missionRoot = view("mission");
  missionRoot.replaceChildren();
  if (missions.length > 1) {
    const overview = element(doc, "section", undefined, "sim-mission-overview");
    overview.append(element(doc, "h3", `Missions (${missions.length})`));
    const list = element(doc, "ul", undefined, "sim-mission-list");
    for (const item of missions) {
      const details = missionProgress?.[item.mission_id];
      list.append(element(doc, "li", `${item.station_name || item.mission_id} · ${details?.demand ?? item.people_count} people · ${details?.confirmed ?? "—"} confirmed · ${details?.pending ?? "—"} pending · ${humanize(details?.status || "Unavailable")}`));
    }
    const label = element(doc, "label", "Inspect mission");
    const selector = element(doc, "select");
    selector.setAttribute("aria-label", "Inspect mission");
    for (const item of missions) {
      const option = element(doc, "option", `${item.station_name || item.mission_id} · ${item.people_count} people`);
      option.value = item.mission_id;
      selector.append(option);
    }
    selector.value = mission?.mission_id || "";
    selector.addEventListener("change", () => onMissionSelect?.(selector.value));
    label.append(selector);
    overview.append(list, label);
    missionRoot.append(overview);
  }
  const header = element(doc, "div", undefined, "sim-mission-heading");
  const titleBlock = element(doc, "div");
  titleBlock.append(element(doc, "p", "MISSION SNAPSHOT", "sim-eyebrow"), element(doc, "h3", mission?.station_name ? `Station ${mission.station_name}` : "Mission progress"));
  header.append(titleBlock, element(doc, "span", humanize(selectedProgress?.status || "Unavailable"), "sim-mission-status"));
  missionRoot.append(header);
  const metrics = element(doc, "div", undefined, "sim-metrics");
  for (const [key, label, helper] of [
    ["demand", "People to rescue", "Total mission demand"],
    ["confirmed", "Confirmed seats", "Guaranteed transport"],
    ["pending", "Pending seats", "Awaiting a response"],
    ["additional_needed", "More seats needed", "Not covered by pending requests"],
  ]) {
    const card = element(doc, "article", undefined, `sim-metric sim-metric-${key}`);
    const number = element(doc, "strong", selectedProgress?.[key] ?? "—");
    number.dataset.metric = key;
    card.append(element(doc, "span", label), number, element(doc, "small", helper));
    metrics.append(card);
  }
  missionRoot.append(metrics);
  const accounting = element(doc, "p", `Unconfirmed demand: ${selectedProgress?.unconfirmed ?? "—"}. Pending requests and temporary quote holds are not confirmed transport.`, "sim-helper sim-accounting-note");
  missionRoot.append(accounting);

  const fleet = view("fleet");
  resetSection(fleet, "Fleet", "Availability and individual commitments at this moment.");
  const ships = array(market.ships);
  if (!ships.length) empty(fleet, "No ships registered at this moment.");
  const fleetGrid = element(doc, "div", undefined, "sim-fleet-grid");
  for (const ship of ships) {
    const available = array(market.availabilities).filter((item) => item.ship_id === ship.ship_id).sort((a, b) => Number(a.recorded_at) - Number(b.recorded_at)).at(-1);
    const card = element(doc, "article", undefined, "sim-ship");
    const shipTitle = element(doc, "div", undefined, "sim-ship-title");
    shipTitle.append(shipIcon(doc), element(doc, "h4", ship.name || ship.ship_id));
    card.append(shipTitle, element(doc, "p", ship.ship_id, "sim-identifier"));
    const facts = element(doc, "dl", undefined, "sim-facts");
    fact(facts, "Availability", available ? available.available ? "Available" : "Unavailable" : "Not published");
    fact(facts, "Reported capacity", available?.total_seats ?? "—");
    fact(facts, "Arrival estimate", available?.arrival_estimate_seconds !== undefined ? `${available.arrival_estimate_seconds}s` : "—");
    card.append(facts);
    const commitments = requests.filter((item) => item.ship_id === ship.ship_id);
    if (!commitments.length) card.append(element(doc, "p", "No requests yet.", "sim-helper"));
    for (const request of commitments) card.append(element(doc, "p", `${humanize(request.outcome)} · requested ${request.requested_seats ?? "—"} · confirmed ${request.confirmed_seats ?? "—"}`, "sim-ship-commitment"));
    fleetGrid.append(card);
  }
  fleet.append(fleetGrid);
  records(fleet, "Availability publications", array(market.availabilities), "No availability publications.");
  records(fleet, "Offer revisions", array(market.offers), "No offers published at this moment.");

  const requestRoot = view("requests");
  resetSection(requestRoot, "Seat requests", "Final outcomes remain closed; only accepted seats count as confirmed.");
  const selectedRequests = array(mission?.requests);
  if (!selectedRequests.length) empty(requestRoot, "No requests submitted for this mission at this moment.");
  else {
    const scroll = element(doc, "div", undefined, "sim-table-scroll");
    scroll.tabIndex = 0;
    scroll.setAttribute("role", "region");
    scroll.setAttribute("aria-label", "Seat requests table");
    const table = element(doc, "table", undefined, "sim-table");
    const caption = element(doc, "caption", "Requests in the selected committed snapshot", "sim-sr-only");
    const head = element(doc, "thead");
    const headingRow = element(doc, "tr");
    for (const label of ["Request / ship", "Requested", "Confirmed", "Outcome"]) {
      const cell = element(doc, "th", label);
      cell.scope = "col";
      headingRow.append(cell);
    }
    head.append(headingRow);
    const body = element(doc, "tbody");
    for (const request of selectedRequests) {
      const row = element(doc, "tr");
      const identity = element(doc, "td");
      identity.append(element(doc, "strong", request.request_id), element(doc, "small", request.ship_id));
      row.append(identity, element(doc, "td", request.requested_seats ?? "—"), element(doc, "td", request.confirmed_seats ?? "—"), element(doc, "td", humanize(request.outcome)));
      body.append(row);
    }
    table.append(caption, head, body);
    scroll.append(table);
    requestRoot.append(scroll);
  }
  records(requestRoot, "Complete request records", selectedRequests, "No request records.");
  records(requestRoot, "Mission history", array(mission?.history), "No mission history entries at this moment.");

  const decisions = view("decisions");
  resetSection(decisions, "Mobilisation decisions", "Solver recommendations are proposals. A request exists only after successful submission.");
  const decisionRecords = array(state.decision_index).filter((entry) => { const id = (entry.decision || entry.result?.value || entry.value || entry).mission_id; return !id || id === mission?.mission_id; });
  if (!decisionRecords.length) empty(decisions, "No solver decisions recorded at this moment.");
  for (const entry of decisionRecords) {
    const decision = entry.decision || entry.result?.value || entry.value || entry;
    const article = element(doc, "article", undefined, "sim-decision");
    article.append(element(doc, "h4", decision.decision_id || entry.decision_id || "Recorded decision"));
    const labels = [decision.status, decision.reason].filter(Boolean).map(humanize).join(" · ");
    if (labels) article.append(element(doc, "p", labels, "sim-helper"));
    const evaluations = array(decision.evaluations || decision.offer_evaluations);
    for (const evaluation of evaluations) {
      article.append(element(doc, "p", `${evaluation.ship_id || evaluation.offer_id || "Candidate"}: ${evaluation.selected === true ? "Selected proposal" : evaluation.selected === false ? "Not selected" : "Evaluation"}${evaluation.proposed_seats !== undefined ? ` · ${evaluation.proposed_seats} seats` : ""}${evaluation.reason ? ` · ${humanize(evaluation.reason)}` : ""}`, "sim-candidate"));
    }
    article.append(recordDetails(doc, entry, "Allocations, evaluations, reasons and full trace"));
    decisions.append(article);
  }

  const communication = view("communication");
  resetSection(communication, "Communication & recovery", "Delivery classifications and session sequencing belong to the recorded API state.");
  records(communication, "Messages", array(state.message_index), "No messages recorded at this moment.", true);
  records(communication, "Deliveries", array(state.delivery_index), "No deliveries recorded at this moment.", true);
  records(communication, "Sessions", array(state.session_index), "No sessions recorded at this moment.", true);

  const other = view("other");
  resetSection(other, "Market & experiments", "Inspect quotes, temporary holds, configured policies and comparison results.");
  records(other, "Quote requests (RFQs)", array(market.rfqs), "Not exercised by this case at the selected time.");
  records(other, "Quotes & temporary holds", array(market.quotes), "Not exercised by this case at the selected time.");
  records(other, "Quote history", array(market.quote_history), "No quote history at the selected time.");
  records(other, "Policies", array(state.policies), "No policies configured at the selected time.");
  records(other, "Scenario configuration", array(state.scenarios), "No experiment scenarios configured for this case.");
  records(other, "Comparison results & timelines", array(state.completed_runs), "No comparisons executed for this case.");
  view("complete-state").textContent = JSON.stringify(state, null, 2);
}

function array(value) { return Array.isArray(value) ? value : []; }
function humanize(value) { return String(value ?? "—").replace(/_/g, " ").replace(/^./, (character) => character.toUpperCase()); }
function element(doc, tag, text, className) { const node = doc.createElement(tag); if (text !== undefined) node.textContent = String(text); if (className) node.className = className; return node; }
function fact(parent, label, value) { parent.append(element(parent.ownerDocument, "dt", label), element(parent.ownerDocument, "dd", value)); }
function resetSection(parent, title, subtitle) { parent.replaceChildren(element(parent.ownerDocument, "h3", title), element(parent.ownerDocument, "p", subtitle, "sim-helper")); }
function empty(parent, text) { parent.append(element(parent.ownerDocument, "p", text, "sim-empty")); }
function recordDetails(doc, value, label) { const details = element(doc, "details", undefined, "sim-record-details"); details.append(element(doc, "summary", label), element(doc, "pre", JSON.stringify(value, null, 2))); return details; }
function records(parent, title, items, emptyText, expanded = false) {
  const doc = parent.ownerDocument;
  const details = element(doc, "details", undefined, "sim-record-group");
  details.open = expanded;
  details.append(element(doc, "summary", `${title} (${items.length})`));
  if (!items.length) empty(details, emptyText);
  items.forEach((item, index) => {
    const projection = Array.isArray(item)
      ? item.length === 3 && typeof item[0] === "string" && item[2]?.delivery_id ? { ...item[2], message_id: item[1] }
        : item.length === 2 && item[0] && typeof item[0] === "object" ? item[0]
          : item.findLast((part) => part && typeof part === "object" && !Array.isArray(part)) || {}
      : item;
    const value = projection.value || projection.result || projection;
    const identity = value.delivery_id || value.message_id || value.session_id || value.availability_id || value.offer_id || value.request_id || value.quote_id || value.rfq_id || value.policy_id || value.scenario_id || `Record ${index + 1}`;
    const status = [value.status, value.outcome, value.disposition, value.classification, value.reason, value.next_inbound !== undefined ? `Next inbound ${value.next_inbound}` : undefined, value.next_outbound !== undefined ? `Next outbound ${value.next_outbound}` : undefined].filter((entry) => typeof entry === "string").map(humanize).join(" · ");
    details.append(recordDetails(doc, item, `Complete ${identity}${status ? ` · ${status}` : ""}`));
  });
  parent.append(details);
}
function shipIcon(doc) {
  const node = doc.createElementNS("http://www.w3.org/2000/svg", "svg");
  node.setAttribute("width", "24"); node.setAttribute("height", "24"); node.setAttribute("viewBox", "0 0 24 24"); node.setAttribute("aria-hidden", "true"); node.setAttribute("fill", "none"); node.setAttribute("stroke", "currentColor"); node.setAttribute("stroke-width", "1.5");
  node.innerHTML = '<path d="M12 3 8 8v8h8V8l-4-5ZM8 12l-4 5h4m8-5 4 5h-4M10 20v1m4-1v1"/><circle cx="12" cy="10" r="1.5"/>';
  return node;
}
